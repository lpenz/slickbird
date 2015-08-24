'''Slickbird dispatcher'''

import os
import logging

import tornado.ioloop
import tornado.web

import ui_methods
from slickbird import datparse
import slickbird.orm as orm


def _log():
    if not _log.logger:
        _log.logger = logging.getLogger(__name__)
    return _log.logger
_log.logger = None


class BaseHandler(tornado.web.RequestHandler):

    def initialize(self, session):
        self.session = session
        self.top = 'http://localhost:8888'
        self.kwpars = {
            'TOP': self.top,
            'MENU': ['collections', 'add'],
        }


class AddHandler(BaseHandler):

    def get(self):
        self.render('add.html', CURMENU='add', **self.kwpars)

    def post(self):
        name = self.get_argument('name')
        filename = self.request.files['datfile'][0]['filename']
        cdb = orm.Collection(name=name, filename=filename)
        self.session.add(cdb)
        self.session.commit()
        games = datparse.parse(
            datstr=self.request.files['datfile'][0]['body'])
        for gn, roms in games.items():
            gdb = orm.Game(collection=cdb, name=gn)
            for rom in roms:
                r = rom['rom']
                r['filename'] = r.pop('name')
                rdb = orm.Rom(game=gdb, **r)
                self.session.add(rdb)
            self.session.add(gdb)
        self.session.commit()
        self.redirect(self.top + '/collection/' + name)


class CollectionsHandler(BaseHandler):

    def get(self):
        self.render('collections.html',
                    collections=self.session.query(orm.Collection),
                    CURMENU='collections',
                    **self.kwpars
                    )


class CollectionHandler(BaseHandler):

    def get(self, collectionname):
        games = {}
        for g in self.session.query(orm.Game).\
                filter(orm.Collection.name == collectionname):
            games[g.name] = True
        self.render('collection.html',
                    collectionname=collectionname,
                    games=games,
                    CURMENU='collections',
                    **self.kwpars
                    )


class MainHandler(BaseHandler):

    def get(self):
        self.redirect(self.top + '/collection')


class Application(tornado.web.Application):

    def __init__(self, *args, **kwargs):
        tornado.web.Application.__init__(self, *args, **kwargs)


def make_app():
    d = dict(session=orm.Session())
    return Application([
        (r'/', MainHandler, d),
        (r'/add', AddHandler, d),
        (r'/collection/?', CollectionsHandler, d),
        (r'/collection/(?P<collectionname>[^/]+)/?', CollectionHandler, d),
    ],
        template_path=os.path.join(os.path.dirname(__file__), 'templates'),
        static_path=os.path.join(os.path.dirname(__file__), 'static'),
        xsrf_cookies=True,
        ui_methods=ui_methods,
        debug=True,
    )
