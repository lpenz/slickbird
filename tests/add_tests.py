'''Test for adding a collection'''

import sys
import os

import tempfile
import json
import requests
import logging
from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor
from tornado.testing import AsyncHTTPTestCase, gen_test

APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(APP_ROOT, '..'))

import slickbird


def _log():
    if not _log.logger:
        _log.logger = logging.getLogger(__name__)
    return _log.logger
_log.logger = None


class TestAdd(AsyncHTTPTestCase):
    executor = ThreadPoolExecutor(max_workers=1)

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        AsyncHTTPTestCase.setUp(self)

    def tearDown(self):
        os.unlink(self.tmp.name)

    def get_app(self):
        return slickbird.make_app(xsrf_cookies=False,
                                  database='sqlite:///' + self.tmp.name)

    @run_on_executor
    def collectionadd(self, name, filename):
        files = {'datfile': open(filename)}
        data = {'name': name}
        return requests.post(self.get_url('/add'), data=data, files=files)

    @gen_test(timeout=300)
    def test_add(self):
        filename = \
            'Nintendo - Game Boy Advance Parent-Clone (20150801-084652).dat'
        addresp = yield self.collectionadd(
            'Game Boy',
            os.path.join(APP_ROOT, 'tests', filename))
        self.assertEqual(addresp.status_code, 200)
        cstatus = None
        while cstatus != 'ready':
            gbresp = yield self.http_client \
                .fetch(self.get_url('/api/collection/Game%20Boy.json'))
            self.assertEqual(gbresp.code, 200)
            c = json.loads(gbresp.body.decode('utf-8'))
            cstatus = c['collection']['status']
            _log().info('collection status {}, games {}'
                        .format(cstatus, len(c['games'])))
