'''Slickbird dispatcher'''

import os
import logging
import tornado.gen
import tornado.ioloop
import tornado.web
from tornado.web import URLSpec
from tornado.options import options, define

import slickbird.orm as orm

from slickbird import hbase
from slickbird import hscanner
from slickbird import hcollection
from slickbird import hgame


def _log():
    if not _log.logger:
        _log.logger = logging.getLogger(__name__)
    return _log.logger
_log.logger = None


# Command-line arguments: ####################################################

define('config', default=None, help='Configuration file')
define('port', default=8888, help='Port to bind to')


# Pages: #####################################################################

class RootHandler(hbase.BaseHandler):

    def get(self):
        self.redirect(self.reverse_url('collection_lst'))


class JsxHandler(hbase.BaseHandler):

    def get(self, jsx):
        self.set_header('Content-Type', 'text/jsx; charset="utf-8"')
        self.render(jsx, **self.kwpars)


# Application: ###############################################################

class Application(tornado.web.Application):

    def __init__(self, *args, **kwargs):
        self.deploydir = kwargs.pop('deploydir', '.')
        tornado.web.Application.__init__(self, *args, **kwargs)


def make_app(xsrf_cookies=False,
             database='sqlite:///db',
             autoreload=True,
             deploydir='.'):
    d = dict(session=orm.make_session(database=database)(),
             deploydir=deploydir)
    app = Application([
        URLSpec(r'/',
                tornado.web.RedirectHandler,
                {'url': '/collection/list'},
                name='root'),
        # JSX:
        URLSpec(r'/(?P<jsx>[^./]+\.jsx$)',
                JsxHandler,
                d,
                name='jsx'),
        # Scanner:
        URLSpec(r'/scanner/add',
                hscanner.ScannerAddHandler,
                d, name='scanner_add'),
        URLSpec(r'/scanner/list',
                hbase.genPageHandler('scanner_lst'),
                d, name='scanner_lst'),
        # Collections:
        URLSpec(r'/collection/add',
                hcollection.CollectionAddHandler,
                d, name='collection_add'),
        URLSpec(r'/collection/list',
                hbase.genPageHandler('collection_lst'),
                d, name='collection_lst'),
        URLSpec(r'/collection/(?P<collectionname>[^/]+)/list',
                hbase.genPageHandler('game_lst'),
                d, name='game_lst'),
        # json API:
        URLSpec(r'/api/scanner_lst.json',
                hscanner.ScannerDataHandler,
                d,
                name='api_scanner_lst'),
        URLSpec(r'/api/collection_lst.json',
                hcollection.CollectionListDataHandler,
                d,
                name='api_collection_lst'),
        URLSpec(r'/api/collection/(?P<collectionname>[^/]+).json',
                hgame.GameListDataHandler,
                d,
                name='api_game_lst'),
    ],
        template_path=os.path.join(os.path.dirname(__file__), 'templates'),
        static_path=os.path.join(os.path.dirname(__file__), 'static'),
        xsrf_cookies=xsrf_cookies,
        debug=True,
        autoreload=autoreload,
        deploydir=deploydir,
    )
    _log().debug(u'app created')
    return app


def start():
    app = make_app()
    app.listen(options.port)
    _log().info(u'slickbird started at port {}'.format(options.port))
    tornado.ioloop.IOLoop.current().start()
