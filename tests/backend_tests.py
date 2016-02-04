'''Slickbird backend tests'''

import os
import json
import tempfile

from slickbird.collectionjson import collectionjson
from slickbird import orm

from tornado.testing import gen_test

from . import base

pjoin = os.path.join
APP_ROOT = os.path.abspath(pjoin(os.path.dirname(__file__), '..'))


class TestSlickbirdBackend(base.TestSlickbirdBase):

    @gen_test
    def test_collectionjson(self):
        yield self.collectionadd(
            'dummy',
            pjoin(APP_ROOT, 'tests/dummytest.dat'))
        tmp = tempfile.NamedTemporaryFile(suffix='.json')
        session = orm.make_session('sqlite:///' + self.db.name)()
        cdb = session.query(orm.Collection)\
            .first()
        collectionjson(cdb, tmp)
        tmp.flush()
        tmp.seek(0)
        json.loads(tmp.read().decode('utf-8'))
        tmp.close()
