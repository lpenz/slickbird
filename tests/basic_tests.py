'''Slickbird basic tests'''

import sys
import os
import json
from lxml import etree

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from tornado.testing import gen_test
import tornado.httpclient

pjoin = os.path.join
APP_ROOT = os.path.abspath(pjoin(os.path.dirname(__file__), '..'))
sys.path.append(pjoin(APP_ROOT, '..'))

from . import base


class TestSlickbirdBase(base.TestSlickbirdBase):

    def assertExists(self, p):
        self.assertTrue(os.path.exists(p))

    @gen_test
    def test_flow(self):
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
        self.assertExists(pjoin(self.deploydir,
                                'dummy',
                                'emptyfile.txt'))
        c = yield self.collectionget('dummy')
        self.assertNotEqual(c['games'][0]['status'], 'missing')
        self.assertEqual(c['games'][1]['status'], 'missing')
        c = yield self.collectionget('dummy', hidemissing=True)
        self.assertEqual(len(c['games']), 1)
        scrapping = True
        while scrapping:
            resp = yield self.http_client\
                .fetch(self.get_url('/api/collection/dummy.json'))
            self.assertEqual(resp.code, 200)
            collectiondata = json.loads(resp.body.decode('utf-8'))
            games = dict([(g['name'], g) for g in collectiondata['games']])
            if games['Kenseiden']['nfo'] != 'missing':
                scrapping = False
        nfofile = pjoin(self.deploydir,
                        'dummy',
                        'emptyfile.nfo')
        self.assertExists(nfofile)
        # print(open(nfofile).read())
        with open(nfofile) as nfofd:
            et = etree.parse(nfofd)
            self.assertEqual('Kenseiden',
                             et.getroot().find('title').text)
            self.assertEqual('1988',
                             et.getroot().find('year').text)

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

    @gen_test
    def test_add_collection_twice(self):
        yield self.collectionadd(
            'dummy',
            pjoin(APP_ROOT, 'tests/dummytest.dat'))
        yield self.collectionadd(
            'dummy',
            pjoin(APP_ROOT, 'tests/dummytest.dat'))
        resp = yield self.http_client\
            .fetch(self.get_url('/api/collection_lst.json'))
        self.assertEqual(resp.code, 200)
        collections = json.loads(resp.body.decode('utf-8'))
        self.assertEqual(len(collections), 1)

    @gen_test
    def test_collection_noname(self):
        yield self.collectionadd(
            '',
            pjoin(APP_ROOT, 'tests/dummytest.dat'))
        resp = yield self.http_client\
            .fetch(self.get_url('/api/collection_lst.json'))
        self.assertEqual(resp.code, 200)
        collections = json.loads(resp.body.decode('utf-8'))
        self.assertEqual(collections[0]['name'], 'Dummy test file')

    @gen_test
    def test_collection_invalid(self):
        try:
            yield self.http_client\
                .fetch(self.get_url('/api/collection/invalid.json'))
            self.assertTrue(False)
        except tornado.httpclient.HTTPError as e:
            self.assertEqual(e.code, 404)

    @gen_test
    def test_scannerclear(self):
        # Create file, scan it:
        with open(pjoin(self.scanningdir, 'emptyfile.txt'), 'w') as fd:
            fd.write('asdf')
        resp = yield self.http_client\
            .fetch(self.get_url('/scanner/add'),
                   method='POST',
                   body=urlencode({'directory': self.scanningdir}),
                   )
        self.assertEqual(resp.code, 200)
        # Get scanner data with file:
        resp = yield self.http_client\
            .fetch(self.get_url('/api/scanner_lst.json'))
        self.assertEqual(resp.code, 200)
        scannerlst = json.loads(resp.body.decode('utf-8'))
        self.assertEqual(len(scannerlst), 1)
        # Clear scanner:
        resp = yield self.http_client\
            .fetch(self.get_url('/api/scanner_clear'),
                   body='',
                   method='POST')
        # Get scanner data without file:
        resp = yield self.http_client\
            .fetch(self.get_url('/api/scanner_lst.json'))
        self.assertEqual(resp.code, 200)
        scannerlst = json.loads(resp.body.decode('utf-8'))
        self.assertEqual(len(scannerlst), 0)
