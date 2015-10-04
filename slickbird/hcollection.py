'''Slickbird collection handler'''

import logging
import json

from tornado.web import URLSpec
import tornado.web

from slickbird import datparse
import slickbird.orm as orm

from slickbird import hbase


def _log():
    if not _log.logger:
        _log.logger = logging.getLogger(__name__)
    return _log.logger
_log.logger = None


# Add handler: ###############################################################

class CollectionAddHandler(hbase.PageHandler):
    name = 'collection_add'

    @tornado.gen.coroutine
    def collectionadd(self, cdb, collection):
        for gn, gd in collection['games'].items():
            gdb = orm.Game(collection=cdb, name=gn, status='missing')
            for variant in gd['variants']:
                vdb = orm.Variant(game=gdb, name=variant['name'])
                self.settings['session'].add(vdb)
                for r in variant['roms']:
                    rdb = orm.Rom(variant=vdb, **r)
                    self.settings['session'].add(rdb)
            _log().debug('add collection {} game {}'
                         .format(cdb.name, gn))
            self.settings['session'].add(gdb)
            yield tornado.gen.moment
        cdb.status = 'ready'
        self.settings['session'].commit()

    @tornado.gen.coroutine
    def post(self):
        name = self.get_argument('name')
        filename = self.request.files['datfile'][0]['filename']
        collection = datparse.parse(
            datstr=self.request.files['datfile'][0]['body'].decode('utf-8'))
        if name == '':
            name = collection['header']['name']
        cdb = self.settings['session'].query(orm.Collection)\
            .filter(orm.Collection.name == name)\
            .first()
        if cdb:
            self.settings['session'].delete(cdb)
        cdb = orm.Collection(
            name=name, filename=filename, status='loading')
        self.settings['session'].add(cdb, collection)
        self.settings['session'].commit()
        self.redirect(self.reverse_url('game_lst', name))
        tornado.ioloop.IOLoop.current() \
            .spawn_callback(self.collectionadd, cdb, collection)


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
