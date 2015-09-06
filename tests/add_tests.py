'''Test for adding a collection'''

import sys
import os

import requests
from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor
from tornado.testing import AsyncHTTPTestCase, gen_test

APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(APP_ROOT, '..'))

import slickbird


class TestAdd(AsyncHTTPTestCase):
    executor = ThreadPoolExecutor(max_workers=2)

    def get_app(self):
        return slickbird.make_app(xsrf_cookies=False)

    def setUp(self):
        AsyncHTTPTestCase.setUp(self)

    @run_on_executor
    def collectionadd(self, name, filename):
        files = {'datfile': open(filename)}
        data = {'name': name}
        return requests.post(self.get_url('/add'), data=data, files=files)

    @gen_test(timeout=90)
    def test_add(self):
        response = yield self.collectionadd('Game Boy', 'Nintendo - Game Boy Advance Parent-Clone (20150801-084652).dat')
        self.assertEqual(response.status_code, 200)

