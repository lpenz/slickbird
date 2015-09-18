'''Slickbird game handler'''

import logging
import json
import os
import re
import io

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
import slickbird.filenames as filenames

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
            .spawn_callback(self.main)

    @tornado.gen.coroutine
    def main(self):
        _log().info('scrapper sleeping')
        yield self.condition.wait()
        _log().info('scrapper woke up')
        changed = True
        while changed:
            changed = yield self.work()
        tornado.ioloop.IOLoop.current()\
            .spawn_callback(self.main)

    @tornado.gen.coroutine
    def work(self):
        changed = False
        for r in self.session.query(orm.Rom)\
                .filter(orm.Rom.local != ''):
            nfofile = filenames.nfo(self.deploydir,
                                    r)
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
            etr = etree.fromstring(response.body)
            for g in etr.findall('./Game'):
                nfo = {}
                for f, xpath in self.FIELDMAP.items():
                    e = g.find(xpath)
                    if e is not None:
                        nfo[f] = e.text
                if 'year' in nfo and nfo['year'] is not None:
                    nfo['year'] = re.sub(
                        '.*([0-9]{4})$', '\\1', nfo['year'])
            etw = etree.Element('game')
            for f in self.FIELDMAP.keys():
                if f in nfo:
                    etree.SubElement(etw, f).text = nfo[f]
            etwstr = etree.tostring(etw,
                                    pretty_print=True)
            with io.open(nfofile, 'w') as fd:
                fd.write(etwstr.decode('utf-8'))
            r.game.nfostatus = 'present'
            _log().info('scrapped nfo {}'.format(nfofile))
            yield tornado.gen.moment
        self.session.commit()
        raise tornado.gen.Return(changed)


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
            for r in dbg.roms:
                nfofile = filenames.nfo(self.settings['deploydir'],
                                        r)
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
