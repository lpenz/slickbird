'''Slickbird collection handler'''

import logging
import json

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
        for gn, roms in collection['games'].items():
            gdb = orm.Game(collection=cdb, name=gn, status='missing')
            for rom in roms:
                r = rom['rom']
                r['filename'] = r.pop('name')
                rdb = orm.Rom(game=gdb, **r)
                self.session.add(rdb)
            _log().debug('add collection {} game {}'
                         .format(cdb.name, gn))
            self.session.add(gdb)
            yield tornado.gen.moment
        cdb.status = 'ready'
        self.session.commit()

    @tornado.gen.coroutine
    def post(self):
        name = self.get_argument('name')
        filename = self.request.files['datfile'][0]['filename']
        collection = datparse.parse(
            datstr=self.request.files['datfile'][0]['body'].decode('utf-8'))
        if name == '':
            name = collection['header']['name']
        cdb = self.session.query(orm.Collection)\
            .filter(orm.Collection.name == name)\
            .first()
        if cdb:
            self.session.delete(cdb)
        cdb = orm.Collection(
            name=name, filename=filename, status='loading')
        self.session.add(cdb, collection)
        self.session.commit()
        self.redirect(self.reverse_url('game_lst', name))
        tornado.ioloop.IOLoop.current() \
            .spawn_callback(self.collectionadd, cdb, collection)


# API: #######################################################################

class CollectionListDataHandler(hbase.BaseHandler):

    def get(self):
        self.write(json.dumps([c.as_dict()
                   for c in self.session.query(orm.Collection)]))
