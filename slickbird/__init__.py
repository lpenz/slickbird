'''Slickbird options importer and core classes'''

import logging
import os
import errno
from lxml import etree
from tornado.options import define, options

import slickbird.orm as orm


# Slickbird option registration: #############################################

define('config', default=None, help='Configuration file')
define('database', default='./db', help='Database file')
define('home', default='.', help='Home directory of colletions')


# Misc functions: ############################################################

def _log():
    if not _log.logger:
        _log.logger = logging.getLogger(__name__)
    return _log.logger
_log.logger = None


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


# Functional classes: ########################################################

class CollectionAdder(object):

    def __init__(self, session, name, directory, filename, dat):
        self.session = session
        if name == '':
            name = dat['header']['name']
        self.name = name
        if directory == '':
            directory = name.replace(' ', '_')
        self.directory = directory
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
        pj = os.path.join
        base = pj(options.home, self.directory)
        mkdir_p(base)
        mkdir_p(pj(base, 'artwork'))
        mkdir_p(pj(base, 'nfos'))
        nfofile = pj(base, 'collection.nfo')
        if not os.path.exists(nfofile):
            nfo = etree.Element('collection')
            etree.SubElement(nfo, 'title').text = self.name
            etree.ElementTree(nfo).write(
                nfofile,
                encoding='utf-8', xml_declaration=True, pretty_print=True)
        self.cdb.status = 'ready'
