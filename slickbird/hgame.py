'''Slickbird game handler'''

import logging
import json

import tornado.escape
from tornado.web import URLSpec

import slickbird.orm as orm

from slickbird import hbase


def _log():
    if not _log.logger:
        _log.logger = logging.getLogger(__name__)
    return _log.logger
_log.logger = None


# API: #######################################################################

class GameListDataHandler(tornado.web.RequestHandler):

    def get(self, collectionname):
        name = tornado.escape.url_unescape(collectionname)
        hidemissing = 'true' == self.get_argument('hidemissing',
                                                  default='false')
        cdb = self.settings['session'].query(orm.Collection)\
            .filter(orm.Collection.name == name)\
            .first()
        if not cdb:
            _log().warn('collection {} not found'
                        .format(name))
            self.send_error(404)
            return
        if hidemissing:
            games = [g.as_dict()
                     for g in cdb.games if g.status != 'missing']
        else:
            games = [g.as_dict() for g in cdb.games]
        _log().debug('returning {} with {} games'
                     .format(name, len(games)))
        self.write(json.dumps({
            'collection': cdb.as_dict(),
            'games': games,
        }))


# Install: ###################################################################

def install(app):
    app.add_handlers('.*', [
        URLSpec(r'/collection/(?P<collectionname>[^/]+)/list',
                hbase.genPageHandler('game_lst'),
                name='game_lst'),
        # json API:
        URLSpec(r'/api/collection/(?P<collectionname>[^/]+).json',
                GameListDataHandler,
                name='api_game_lst'),
    ])
