'''slickbird tests'''

import sys
import os
import shutil
import tempfile
import json
import requests
import logging

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from requests.utils import quote
from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor
from tornado import gen
from tornado.testing import AsyncHTTPTestCase, gen_test

pjoin = os.path.join
APP_ROOT = os.path.abspath(pjoin(os.path.dirname(__file__), '..'))
sys.path.append(pjoin(APP_ROOT, '..'))

import slickbird


def _log():
    if not _log.logger:
        _log.logger = logging.getLogger(__name__)
    return _log.logger
_log.logger = None


class TestSlickbird(AsyncHTTPTestCase):
    executor = ThreadPoolExecutor(max_workers=1)

    def setUp(self):
        self.db = tempfile.NamedTemporaryFile(delete=False)
        self.deploydir = tempfile.mkdtemp()
        self.scanningdir = tempfile.mkdtemp()
        AsyncHTTPTestCase.setUp(self)

    def tearDown(self):
        os.unlink(self.db.name)
        shutil.rmtree(self.deploydir, ignore_errors=True)
        shutil.rmtree(self.scanningdir, ignore_errors=True)

    def get_app(self):
        return slickbird.make_app(xsrf_cookies=False,
                                  database='sqlite:///' + self.db.name,
                                  autoreload=False,
                                  deploydir=self.deploydir,
                                  )

    @run_on_executor
    def collectionadd_bg(self, name, filename):
        files = {'datfile': open(filename)}
        data = {'name': name}
        return requests.post(self.get_url('/add'), data=data, files=files)

    @gen.coroutine
    def collectionadd(self, name, filename):
        addresp = yield self.collectionadd_bg(
            name,
            filename)
        self.assertEqual(addresp.status_code, 200)
        cstatus = None
        while cstatus != 'ready':
            resp = yield self.http_client \
                .fetch(self.get_url('/api/collection/{}.json'
                                    .format(quote(name))))
            self.assertEqual(resp.code, 200)
            c = json.loads(resp.body.decode('utf-8'))
            cstatus = c['collection']['status']
        raise gen.Return(c)

    @gen_test(timeout=300)
    def test_bigdatadd(self):
        filename = \
            'Nintendo - Game Boy Advance Parent-Clone (20150801-084652).dat'
        c = yield self.collectionadd(
            'Game Boy',
            pjoin(APP_ROOT, 'tests', filename))
        _log().info('collection status {}, games {}'
                    .format(c['collection']['status'], len(c['games'])))

    @gen_test
    def test_dummyscanner(self):
        c = yield self.collectionadd(
            'dummy',
            pjoin(APP_ROOT, 'tests/dummytest.dat'))
        self.assertEqual(len(c['games']), 1)
        self.assertEqual(c['games'][0]['status'], 'missing')
        self.assertFalse(
            os.path.exists(pjoin(self.deploydir, 'emptyfile.txt')))
        f = open(pjoin(self.scanningdir, 'emptyfile1.txt'), 'w')
        f.close()
        resp = yield self.http_client\
            .fetch(self.get_url('/scanner'),
                   method='POST',
                   body=urlencode({'directory': self.scanningdir}),
                   )
        self.assertEqual(resp.code, 200)
        fps = 'scanner'
        while fps == 'scanner':
            resp = yield self.http_client\
                .fetch(self.get_url('/api/scanner.json'))
            self.assertEqual(resp.code, 200)
            fp = json.loads(resp.body.decode('utf-8'))
            self.assertEqual(len(fp), 1)
            self.assertEqual(
                os.path.basename(fp[0]['filename']), 'emptyfile1.txt')
            fps = fp[0]['status']
        self.assertEqual(fps, 'moved')
        self.assertTrue(
            os.path.exists(pjoin(self.deploydir,
                                 'dummy',
                                 'emptyfile.txt')))
