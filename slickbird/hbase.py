'''Slickbird base handler class and functions'''

import tornado.gen
import tornado.ioloop
import tornado.web


# Base class for handlers: ###################################################

class BaseHandler(tornado.web.RequestHandler):

    def initialize(self, session, deploydir):
        self.session = session
        self.deploydir = deploydir
        self.kwpars = {}


# Pages: #####################################################################

class PageHandler(BaseHandler):

    def get(self, **kwargs):
        kwargs.update(self.kwpars)
        self.render(self.name + '.html', **kwargs)


def genPageHandler(name):
    c = type('PageHandler_' + name, (PageHandler,), {})
    c.name = name
    return c
