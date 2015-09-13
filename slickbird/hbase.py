'''Slickbird base handler class and functions'''

import tornado.gen
import tornado.ioloop
import tornado.web


# Pages: #####################################################################

class PageHandler(tornado.web.RequestHandler):

    def get(self, **kwargs):
        kwargs.update(self.settings)
        self.render(self.name + '.html', **kwargs)


def genPageHandler(name):
    c = type('PageHandler_' + name, (PageHandler,), {})
    c.name = name
    return c
