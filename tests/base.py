'''Slickbird base class for tests'''

import sys
import re
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

try:
    import slickbird.web
except ImportError:
    osp = os.path
    APP_ROOT = osp.abspath(osp.join(osp.dirname(__file__), '..'))
    sys.path.append(osp.join(APP_ROOT, '..'))
    import slickbird.web


class TestSlickbirdBase(AsyncHTTPTestCase):
    executor = ThreadPoolExecutor(max_workers=1)

    def setUp(self):
        self.db = tempfile.NamedTemporaryFile(delete=False)
        self.home = tempfile.mkdtemp()
        self.scanningdir = tempfile.mkdtemp()
        AsyncHTTPTestCase.setUp(self)

    def tearDown(self):
        os.unlink(self.db.name)
        shutil.rmtree(self.home, ignore_errors=True)
        shutil.rmtree(self.scanningdir, ignore_errors=True)
        shutil.rmtree(self.scanningdir, ignore_errors=True)

    def get_app(self):
        return slickbird.web.make_app(xsrf_cookies=False,
                                      database='sqlite:///' + self.db.name,
                                      autoreload=False,
                                      home=self.home,
                                      )

    @run_on_executor
    def collectionadd_bg(self, name, filename):
        files = {'datfile': open(filename)}
        data = {'name': name, 'directory': name}
        return requests.post(self.get_url('/collection/add'),
                             data=data,
                             files=files)

    @gen.coroutine
    def collectionadd(self, name, filename):
        addresp = yield self.collectionadd_bg(
            name,
            filename)
        self.assertEqual(addresp.status_code, 200)
        name = re.sub(r'''.*/collection/([^/]+)/list''',
                      '\\1',
                      addresp.url)
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
