'''Slickbird basic tests'''

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

from . import base


class TestSlickbirdBase(base.TestSlickbirdBase):

    @gen_test
    def test_dummyscanner(self):
        c = yield self.collectionadd(
            'dummy',
            pjoin(APP_ROOT, 'tests/dummytest.dat'))
        self.assertEqual(len(c['games']), 2)
        self.assertEqual(c['games'][0]['status'], 'missing')
        self.assertEqual(c['games'][1]['status'], 'missing')
        self.assertFalse(
            os.path.exists(pjoin(self.deploydir, 'emptyfile.txt')))
        f = open(pjoin(self.scanningdir, 'emptyfile.txt'), 'w')
        f.close()
        f = open(pjoin(self.scanningdir, 'zfile.txt'), 'w')
        f.write('z\n')
        f.close()
        resp = yield self.http_client\
            .fetch(self.get_url('/scanner/add'),
                   method='POST',
                   body=urlencode({'directory': self.scanningdir}),
                   )
        self.assertEqual(resp.code, 200)
        scanning = True
        while scanning:
            resp = yield self.http_client\
                .fetch(self.get_url('/api/scanner_lst.json'))
            self.assertEqual(resp.code, 200)
            scannerlst = json.loads(resp.body.decode('utf-8'))
            self.assertEqual(len(scannerlst), 2)
            scannerdict = dict([(os.path.basename(s['filename']), s)
                               for s in scannerlst])
            self.assertEqual(set(scannerdict.keys()),
                             set(['emptyfile.txt', 'zfile.txt']))
            scanning = any([s['status'] == 'scanning' for s in scannerlst])
        self.assertTrue(
            os.path.exists(pjoin(self.deploydir,
                                 'dummy',
                                 'emptyfile.txt')))
        c = yield self.collectionget('dummy')
        self.assertNotEqual(c['games'][0]['status'], 'missing')
        self.assertEqual(c['games'][1]['status'], 'missing')
        c = yield self.collectionget('dummy', hidemissing=True)
        self.assertEqual(len(c['games']), 1)

    @gen_test
    def test_static_urls(self):
        for f in [
            '',
            'collection_lst.jsx',
            'game_lst.jsx',
            'scanner_lst.jsx',
            'collection/add',
            'collection/list',
            'scanner/add',
            'scanner/list',
        ]:
            resp = yield self.http_client\
                .fetch(self.get_url('/{}'.format(f)))
            self.assertEqual(resp.code, 200)
