'''Slickbird dispatcher'''

import os

import tornado.ioloop
import tornado.web

import ui_methods

from slickbird import datparse

collection = {}


class AddHandler(tornado.web.RequestHandler):

    def get(self):
        self.render('add.html', pos='Add')

    def post(self):
        name = self.get_argument('newcollectionName')
        global collection
        collection[name] = datparse.parse(
            datstr=self.request.files['newcollectionDat'][0]['body']
        )
        self.redirect('/collection/' + name)


class CollectionHandler(tornado.web.RequestHandler):

    def get(self, collectionname):
        self.render('collection.html',
                    pos='Home',
                    collectionname=collectionname,
                    games=collection[collectionname])


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        global collection
        self.render('index.html', pos='Home', collection=collection)


class Application(tornado.web.Application):

    def __init__(self, *args, **kwargs):
        tornado.web.Application.__init__(self, *args, **kwargs)


def make_app():
    return Application([
        (r'/', MainHandler),
        (r'/add', AddHandler),
        (r'/collection/(?P<collectionname>[^/]+)/?', CollectionHandler),
    ],
        template_path=os.path.join(os.path.dirname(__file__), 'templates'),
        # static_path=os.path.join(os.path.dirname(__file__), 'static'),
        xsrf_cookies=True,
        ui_methods=ui_methods,
        debug=True,
    )
