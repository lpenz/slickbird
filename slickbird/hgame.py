'''Slickbird game handler'''

import logging
import json
import os
import re

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote
from lxml import etree

import tornado.escape
import tornado.httpclient
from tornado.web import URLSpec
from tornado.locks import Condition

import slickbird.orm as orm

from slickbird import hbase

pjoin = os.path.join


def _log():
    if not _log.logger:
        _log.logger = logging.getLogger(__name__)
    return _log.logger
_log.logger = None


# Game scrapper coroutine: ###################################################

class GameScrapperWorker(object):
    FIELDMAP = {
        'title': './GameTitle',
        'year': './ReleaseDate',
        'publisher': './Publisher',
        'platform': './Platform',
        'genre': './Genres/genre',
        'plot': './Overview',
    }

    def __init__(self, session, deploydir):
        self.session = session
        self.deploydir = deploydir
        self.condition = Condition()
        tornado.ioloop.IOLoop.current()\
            .spawn_callback(self.work)

    @tornado.gen.coroutine
    def work(self):
        _log().info('scrapper sleeping')
        yield self.condition.wait()
        _log().info('scrapper woke up')
        changed = True
        while changed:
            changed = False
            for r in self.session.query(orm.Rom)\
                    .filter(orm.Rom.local != ''):
                nfofile = re.sub('\.[^.]+$',
                                 '.nfo',
                                 pjoin(self.deploydir,
                                       r.game.collection.name,
                                       r.filename))
                if os.path.exists(nfofile):
                    continue
                changed = True
                url = 'http://thegamesdb.net/api/GetGame.php?exactname=' + \
                    quote(r.game.name)
                http = tornado.httpclient.AsyncHTTPClient()
                response = yield http.fetch(url)
                if response.code != 200:
                    _log().warn('error scrapping {}: {}'
                                .format(r.game.name, str(response)))
                    continue
                et = etree.fromstring(response.body)
                for g in et.findall('./Game'):
                    nfo = {}
                    for f, xpath in self.FIELDMAP.items():
                        e = g.find(xpath)
                        if e is not None:
                            nfo[f] = e.text
                    if 'year' in nfo and nfo['year'] is not None:
                        nfo['year'] = re.sub(
                            '.*([0-9]{4})$', '\\1', nfo['year'])
                with open(nfofile, 'w') as fd:
                    fd.write(etree.tostring(et, pretty_print=True))
                r.game.nfostatus = 'present'
                _log().info('scrapped nfo {}'.format(nfofile))
                yield tornado.gen.moment
        self.session.commit()
        tornado.ioloop.IOLoop.current()\
            .spawn_callback(self.work)


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
        games = []
        for dbg in cdb.games:
            if hidemissing and dbg.status == 'missing':
                continue
            g = dbg.as_dict()
            g['nfo'] = 'missing'
            dstd = pjoin(self.settings['deploydir'],
                         dbg.collection.name)
            for r in dbg.roms:
                nfofile = re.sub('\.[^.]+$',
                                 '.nfo',
                                 pjoin(dstd, r.filename))
                if os.path.exists(nfofile):
                    g['nfo'] = 'present'
                    break
            games.append(g)
        _log().debug('returning {} with {} games'
                     .format(name, len(games)))
        self.write(json.dumps({
            'collection': cdb.as_dict(),
            'games': games,
        }))


# Install: ###################################################################

def install(app):
    w = GameScrapperWorker(app.settings['session'],
                           app.settings['deploydir'])
    app.add_handlers('.*', [
        URLSpec(r'/collection/(?P<collectionname>[^/]+)/list',
                hbase.genPageHandler('game_lst'),
                name='game_lst'),
        # json API:
        URLSpec(r'/api/collection/(?P<collectionname>[^/]+).json',
                GameListDataHandler,
                name='api_game_lst'),
    ])
    app.settings['scrapper'] = w
