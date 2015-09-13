'''Slickbird base class for tests'''

import sys
import os
import shutil
import tempfile
import json
import requests

from requests.utils import quote
from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor
from tornado import gen
from tornado.testing import AsyncHTTPTestCase

pjoin = os.path.join
APP_ROOT = os.path.abspath(pjoin(os.path.dirname(__file__), '..'))
sys.path.append(pjoin(APP_ROOT, '..'))

import slickbird


class TestSlickbirdBase(AsyncHTTPTestCase):
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
        return requests.post(self.get_url('/collection/add'),
                             data=data,
                             files=files)

    @gen.coroutine
    def collectionadd(self, name, filename):
        addresp = yield self.collectionadd_bg(
            name,
            filename)
        self.assertEqual(addresp.status_code, 200)
        c = yield self.collectionget(name)
        raise gen.Return(c)

    @gen.coroutine
    def collectionget(self, name, hidemissing=False):
        cstatus = None
        while cstatus != 'ready':
            resp = yield self.http_client \
                .fetch(self.get_url('/api/collection/{}.json?hidemissing={}'
                                    .format(
                                        quote(name),
                                        str(hidemissing).lower())))
            self.assertEqual(resp.code, 200)
            c = json.loads(resp.body.decode('utf-8'))
            cstatus = c['collection']['status']
        raise gen.Return(c)
