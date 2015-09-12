'''Slickbird dispatcher'''

import os
import logging
import tornado.gen
import tornado.ioloop
import tornado.web
from tornado.web import URLSpec
from tornado.options import options, define

import slickbird.orm as orm

from . import ui_methods

from slickbird import hbase
from slickbird import hscanner
from slickbird import hcollection


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

    def initialize(self, session, name, deploydir):
        self.name = name
        self.session = session
        self.deploydir = deploydir
        self.kwpars = {
            'MENU': ['collections', 'add', 'scanner'],
        }


# Pages: #####################################################################

class TopHandler(hbase.BaseHandler):

    def get(self):
        self.redirect(self.reverse_url('collections'))


# Application: ###############################################################

class Application(tornado.web.Application):

    def __init__(self, *args, **kwargs):
        self.deploydir = kwargs.pop('deploydir', '.')
        tornado.web.Application.__init__(self, *args, **kwargs)


def make_app(xsrf_cookies=False,
             database='sqlite:///db',
             autoreload=True,
             deploydir='.'):
    d0 = dict(session=orm.make_session(database=database)())
    d = lambda n: dict(d0, deploydir=deploydir, name=n)
    return Application([
        URLSpec(r'/',
                TopHandler,
                d(''), name='top'),
        URLSpec(r'/add',
                hcollection.AddHandler,
                d('add'), name='add'),
        URLSpec(r'/scanner',
                hscanner.ScannerHandler,
                d('scanner'), name='scanner'),
        URLSpec(r'/collection',
                hbase.PageHandler,
                d('collections'), name='collections'),
        URLSpec(r'/collection/(?P<collectionname>[^/]+)',
                hcollection.CollectionHandler,
                d('collection'), name='collection'),

        URLSpec(r'/api/collections.json',
                hcollection.CollectionsDataHandler,
                d('collections'),
                name='api_collections'),
        URLSpec(r'/api/collection/(?P<collectionname>[^/]+).json',
                hcollection.CollectionDataHandler,
                d('collection'),
                name='api_collection'),
        URLSpec(r'/api/scanner.json',
                hscanner.ScannerDataHandler,
                d('scanner'),
                name='api_scanner'),
    ],
        template_path=os.path.join(os.path.dirname(__file__), 'templates'),
        static_path=os.path.join(os.path.dirname(__file__), 'static'),
        xsrf_cookies=xsrf_cookies,
        ui_methods=ui_methods,
        debug=True,
        autoreload=autoreload,
        deploydir=deploydir,
    )


def start():
    app = make_app()
    app.listen(options.port)
    _log().info(u'slickbird started at port {}'.format(options.port))
    tornado.ioloop.IOLoop.current().start()
