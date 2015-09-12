'''Slickbird game handler'''

import logging
import json

import slickbird.orm as orm

from slickbird import hbase


def _log():
    if not _log.logger:
        _log.logger = logging.getLogger(__name__)
    return _log.logger
_log.logger = None


# API: #######################################################################

class GameListDataHandler(hbase.BaseHandler):

    def get(self, collectionname):
        cdb = self.session.query(orm.Collection)\
            .filter(orm.Collection.name == collectionname)\
            .first()
        games = []
        if cdb:
            games = [g.as_dict() for g in cdb.games]
        _log().debug('returning {} with {} games'
                     .format(collectionname, len(games)))
        self.write(json.dumps({
            'collection': cdb.as_dict(),
            'games': games,
        }))
