'''Slickbird base handler class and functions'''

import logging
import tornado.gen
import tornado.ioloop
import tornado.web


def _log():
    if not _log.logger:
        _log.logger = logging.getLogger(__name__)
    return _log.logger
_log.logger = None


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

class PageHandler(BaseHandler):

    def get(self):
        self.render(self.name + '.html', CURMENU=self.name, **self.kwpars)
