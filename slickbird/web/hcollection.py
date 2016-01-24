'''Slickbird collection handler'''

import logging
import json

from tornado.web import URLSpec
import tornado.web

from slickbird import datparse
import slickbird.orm as orm

import slickbird
from slickbird.web import hbase


def _log():
    if not _log.logger:
        _log.logger = logging.getLogger(__name__)
    return _log.logger
_log.logger = None


# Add handler: ###############################################################

class CollectionAddHandler(hbase.PageHandler):
    name = 'collection_add'

    @tornado.gen.coroutine
    def collectionadd(self, cadder, dat):
        for gn, gd in dat['games'].items():
            cadder.game_add(gn, gd)
            yield tornado.gen.moment
        cadder.done()
        self.settings['session'].commit()

    @tornado.gen.coroutine
    def post(self):
        name = self.get_argument('name')
        directory = self.get_argument('directory')
        filename = self.request.files['datfile'][0]['filename']
        dat = datparse.parse(
            datstr=self.request.files['datfile'][0]['body'].decode('utf-8'))
        cadder = slickbird.CollectionAdder(
            self.settings['session'], self.settings['home'],
            name, directory, filename, dat)
        self.redirect(self.reverse_url('game_lst', cadder.name))
        tornado.ioloop.IOLoop.current() \
            .spawn_callback(self.collectionadd, cadder, dat)


# API: #######################################################################

class CollectionListDataHandler(tornado.web.RequestHandler):

    def get(self):
        self.write(json.dumps([c.as_dict()
                   for c in self.settings['session'].query(orm.Collection)]))


# Install: ###################################################################

def install(app):
    app.add_handlers('.*', [
        URLSpec(r'/collection/add',
                CollectionAddHandler,
                name='collection_add'),
        URLSpec(r'/collection/list',
                hbase.genPageHandler('collection_lst'),
                name='collection_lst'),
        URLSpec(r'/api/collection_lst.json',
                CollectionListDataHandler,
                name='api_collection_lst'),
    ])
