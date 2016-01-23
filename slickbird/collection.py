'''Slickbird collection lib'''

import logging

import slickbird.orm as orm


def _log():
    if not _log.logger:
        _log.logger = logging.getLogger(__name__)
    return _log.logger
_log.logger = None


# Adder class: ###############################################################

class CollectionAdder(object):

    def __init__(self, session, name, directory, filename, dat):
        self.session = session
        if name == '':
            name = dat['header']['name']
        self.name = name
        if directory == '':
            directory = name.replace(' ', '_')
        cdb = session.query(orm.Collection)\
            .filter(orm.Collection.name == name)\
            .first()
        if cdb:
            session.delete(cdb)
        self.cdb = orm.Collection(
            name=name, directory=directory,
            filename=filename, status='loading')
        session.add(self.cdb)
        session.commit()

    def game_add(self, gn, gd):
        gdb = orm.Game(collection=self.cdb, name=gn, status='missing')
        for variant in gd['variants']:
            vdb = orm.Variant(game=gdb, name=variant['name'])
            self.session.add(vdb)
            for r in variant['roms']:
                rdb = orm.Rom(variant=vdb, **r)
                self.session.add(rdb)
        _log().debug('add collection {} game {}'
                     .format(self.cdb.name, gn))
        self.session.add(gdb)

    def done(self):
        self.cdb.status = 'ready'
