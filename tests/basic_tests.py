'''Slickbird base tests'''

import sys
import os
import json

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from tornado.testing import gen_test

pjoin = os.path.join
APP_ROOT = os.path.abspath(pjoin(os.path.dirname(__file__), '..'))
sys.path.append(pjoin(APP_ROOT, '..'))

from . import common


class TestSlickbirdBase(common.TestSlickbirdBase):
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
