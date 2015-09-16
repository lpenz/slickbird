'''Slickbird dispatcher'''

import os
import logging
import tornado.gen
import tornado.ioloop
import tornado.web
from tornado.web import URLSpec
from tornado.options import options, define

import slickbird.orm as orm

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

class RootHandler(tornado.web.RequestHandler):

    def get(self):
        self.redirect(self.reverse_url('collection_lst'))


class JsxHandler(tornado.web.RequestHandler):

    def get(self, jsx):
        self.set_header('Content-Type', 'text/jsx; charset="utf-8"')
        self.render(jsx, **self.settings)


# Application: ###############################################################

def make_app(xsrf_cookies=False,
             database='sqlite:///db',
             autoreload=True,
             deploydir='.'):
    session = orm.make_session(database=database)()
    app = tornado.web.Application([
        URLSpec(r'/',
                tornado.web.RedirectHandler,
                {'url': '/collection/list'},
                name='root'),
        # JSX:
        URLSpec(r'/(?P<jsx>[^./]+\.jsx$)',
                JsxHandler,
                name='jsx'),
    ],
        template_path=os.path.join(os.path.dirname(__file__), 'templates'),
        static_path=os.path.join(os.path.dirname(__file__), 'static'),
        xsrf_cookies=xsrf_cookies,
        debug=True,
        autoreload=autoreload,
        session=session,
        deploydir=deploydir,
    )
    hcollection.install(app)
    hgame.install(app)
    hscanner.install(app)
    _log().debug(u'app created')
    return app


def start():
    app = make_app()
    app.listen(options.port)
    _log().info(u'slickbird started at port {}'.format(options.port))
    tornado.ioloop.IOLoop.current().start()
