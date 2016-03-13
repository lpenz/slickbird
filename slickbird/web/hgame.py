'''Slickbird game handler'''

import logging
import json
import os

import tornado.escape
import tornado.httpclient
from tornado.web import URLSpec
from tornado.locks import Condition

import slickbird.orm as orm
import slickbird.filenames as filenames
from slickbird.scrapper import Scrapper

pjoin = os.path.join


def _log():
    if not _log.logger:
        _log.logger = logging.getLogger(__name__)
    return _log.logger
_log.logger = None


# Pages: #####################################################################

class GameListPageHandler(tornado.web.RequestHandler):

    def get(self, collectionname):
        cdb = self.settings['session'].query(orm.Collection)\
            .filter(orm.Collection.name == collectionname)\
            .first()
        if not cdb:
            self.send_error(404)
            return
        kwargs = {'collectionname': collectionname}
        kwargs.update(self.settings)
        self.render('game_lst.html', **kwargs)

# Game scrapper coroutine: ###################################################


class GameScrapperWorker(object):

    def __init__(self, session, home):
        self.scrapper = Scrapper(session, home)
        self.session = session
        self.home = home
        self.condition = Condition()
        tornado.ioloop.IOLoop.current()\
            .spawn_callback(self.main)

    @tornado.gen.coroutine
    def main(self):
        _log().info('scrapper sleeping')
        yield self.condition.wait()
        _log().info('scrapper woke up')
        self.scrapper.scrap_missing()
        tornado.ioloop.IOLoop.current()\
            .spawn_callback(self.main)
        raise tornado.gen.Return(False)


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
            _log().warning('collection {} not found'
                           .format(name))
            self.send_error(404)
            return
        games = []
        for dbg in cdb.games:
            if hidemissing and dbg.status == 'missing':
                continue
            g = dbg.as_dict()
            g['nfo'] = 'missing'
            for v in dbg.variants:
                nfofile = filenames.nfo(self.settings['home'],
                                        v)
                if os.path.exists(nfofile):
                    g['nfo'] = 'present'
                    break
            games.append(g)
        _log().debug('returning {} with {} games'
                     .format(name, len(games)))
        # _log().debug(json.dumps(games, indent=4))
        self.write(json.dumps({
            'collection': cdb.as_dict(),
            'games': games,
        }))


class GameListReloadHandler(tornado.web.RequestHandler):

    def post(self, collectionname):
        name = tornado.escape.url_unescape(collectionname)
        _log().info('reloading {}'.format(name))
        cdb = self.settings['session'].query(orm.Collection)\
            .filter(orm.Collection.name == name)\
            .first()
        cdb.status = 'ready'
        self.settings['session'].commit()
        if not cdb:
            _log().warning('collection {} not found'
                           .format(name))
            self.send_error(404)
            return
        for dbg in cdb.games:
            found = False
            for v in dbg.variants:
                vfile = filenames.variant(self.settings['home'],
                                          v)
                if os.path.exists(vfile):
                    found = True
            if found:
                dbg.status = 'ok'
            else:
                dbg.status = 'missing'
        self.write(json.dumps({'result': True}))


class GameScrapperHandler(tornado.web.RequestHandler):

    def post(self):
        self.settings['scrapper'].condition.notify()
        self.write(json.dumps({'result': True}))


# Install: ###################################################################

def install(app):
    w = GameScrapperWorker(app.settings['session'],
                           app.settings['home'])
    app.add_handlers('.*', [
        URLSpec(r'/collection/(?P<collectionname>[^/]+)/list',
                GameListPageHandler,
                name='game_lst'),
        # json API:
        URLSpec(r'/api/collection/(?P<collectionname>[^/]+).json',
                GameListDataHandler,
                name='api_game_lst'),
        URLSpec(r'/api/collection/(?P<collectionname>[^/]+)/reload',
                GameListReloadHandler,
                name='api_game_reload'),
        URLSpec(r'/api/scrapper',
                GameScrapperHandler,
                name='api_scrap'),
    ])
    app.settings['scrapper'] = w
