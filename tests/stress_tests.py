'''Slickbird stress tests'''

import os
import logging

from tornado.testing import gen_test

from . import base

pjoin = os.path.join
APP_ROOT = os.path.abspath(pjoin(os.path.dirname(__file__), '..'))


def _log():
    if not _log.logger:
        _log.logger = logging.getLogger(__name__)
    return _log.logger
_log.logger = None


class TestSlickbirdStress(base.TestSlickbirdBase):
    @gen_test(timeout=300)
    def test_bigdatadd(self):
        filename = \
            'Nintendo - Game Boy Advance Parent-Clone (20150801-084652).dat'
        c = yield self.collectionadd(
            'Game Boy',
            pjoin(APP_ROOT, 'tests', filename))
        _log().info('collection status {}, games {}'
                    .format(c['collection']['status'], len(c['games'])))
