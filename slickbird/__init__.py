'''Slickbird dispatcher'''

import os
import logging
import json

import tornado.gen
import tornado.ioloop
import tornado.web
from tornado.web import URLSpec
from tornado.options import options, define

from slickbird import datparse
import slickbird.orm as orm

from . import ui_methods


def _log():
    if not _log.logger:
        _log.logger = logging.getLogger(__name__)
    return _log.logger
_log.logger = None


# Command-line arguments: ####################################################

define('config', default=None, help='Configuration file')
define('port', default=8888, help='Port to bind to')


# Base class for handlers: ###################################################

class BaseHandler(tornado.web.RequestHandler):

    def initialize(self, session, name):
        self.name = name
        self.session = session
        self.kwpars = {
            'MENU': ['collections', 'add'],
        }


# Pages: #####################################################################

class PageHandler(BaseHandler):

    def get(self):
        self.render(self.name + '.html', CURMENU=self.name, **self.kwpars)


class TopHandler(BaseHandler):

    def get(self):
        self.redirect(self.reverse_url('collections'))


class AddHandler(PageHandler):

    @tornado.gen.coroutine
    def collectionadd(self, cdb, collection):
        for gn, roms in collection['games'].items():
            gdb = orm.Game(collection=cdb, name=gn)
            for rom in roms:
                r = rom['rom']
                r['filename'] = r.pop('name')
                rdb = orm.Rom(game=gdb, **r)
                self.session.add(rdb)
            _log().debug('add collection {} game {}'
                         .format(cdb.name, gn))
            self.session.add(gdb)
            yield tornado.gen.moment
        cdb.status = 'ready'
        self.session.commit()

    @tornado.gen.coroutine
    def post(self):
        name = self.get_argument('name')
        filename = self.request.files['datfile'][0]['filename']
        collection = datparse.parse(
            datstr=self.request.files['datfile'][0]['body'].decode('utf-8'))
        if name == '':
            name = collection['header']['name']
        cdb = self.session.query(orm.Collection)\
            .filter(orm.Collection.name == name)\
            .first()
        if cdb:
            self.session.delete(cdb)
        cdb = orm.Collection(
            name=name, filename=filename, status='loading')
        self.session.add(cdb, collection)
        self.session.commit()
        self.redirect(self.reverse_url('collection', name))
        tornado.ioloop.IOLoop.current() \
            .spawn_callback(self.collectionadd, cdb, collection)


class CollectionHandler(PageHandler):

    def get(self, collectionname):
        self.render('collection.html',
                    collectionname=collectionname,
                    CURMENU='collections',
                    **self.kwpars
                    )


# API: #######################################################################

class CollectionsDataHandler(BaseHandler):

    def get(self):
        self.write(json.dumps([c.as_dict()
                   for c in self.session.query(orm.Collection)]))


class CollectionDataHandler(BaseHandler):

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


# Application: ###############################################################

class Application(tornado.web.Application):

    def __init__(self, *args, **kwargs):
        tornado.web.Application.__init__(self, *args, **kwargs)


def make_app(xsrf_cookies=False, database='sqlite:///db', autoreload=True):
    d0 = dict(session=orm.make_session(database=database)())
    d = lambda n: dict(d0, name=n)
    return Application([
        URLSpec(r'/',
                TopHandler,
                d(''), name='top'),
        URLSpec(r'/add/?', AddHandler,
                d('add'), name='add'),
        URLSpec(r'/collection/?',
                PageHandler,
                d('collections'), name='collections'),
        URLSpec(r'/collection/(?P<collectionname>[^/]+)/?',
                CollectionHandler,
                d('collection'), name='collection'),

        URLSpec(r'/api/collections.json',
                CollectionsDataHandler,
                d('collections'),
                name='api_collections'),
        URLSpec(r'/api/collection/(?P<collectionname>[^/]+).json',
                CollectionDataHandler,
                d('collection'),
                name='api_collection'),
    ],
        template_path=os.path.join(os.path.dirname(__file__), 'templates'),
        static_path=os.path.join(os.path.dirname(__file__), 'static'),
        xsrf_cookies=xsrf_cookies,
        ui_methods=ui_methods,
        debug=True,
        autoreload=autoreload,
    )


def start():
    app = make_app()
    app.listen(options.port)
    _log().info(u'slickbird started at port {}'.format(options.port))
    tornado.ioloop.IOLoop.current().start()
