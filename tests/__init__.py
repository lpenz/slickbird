'''slickbird tests'''

import sys
import os
import shutil
import tempfile
import json
import requests
import logging
from requests.utils import quote
from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor
from tornado import gen
from tornado.testing import AsyncHTTPTestCase, gen_test

APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(APP_ROOT, '..'))

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
        AsyncHTTPTestCase.setUp(self)

    def tearDown(self):
        os.unlink(self.db.name)
        shutil.rmtree(self.deploydir, ignore_errors=True)

    def get_app(self):
        return slickbird.make_app(xsrf_cookies=False,
                                  database='sqlite:///' + self.db.name,
                                  autoreload=False,
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
            os.path.join(APP_ROOT, 'tests', filename))
        _log().info('collection status {}, games {}'
                    .format(c['collection']['status'], len(c['games'])))

    @gen_test
    def test_dummyadd(self):
        c = yield self.collectionadd(
            'dummy',
            os.path.join(APP_ROOT, 'tests/dummytest.dat'))
        self.assertEqual(len(c['games']), 1)
