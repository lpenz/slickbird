'''Slickbird options importer and core classes'''

import logging
import os
import errno
import binascii
import shutil
from lxml import etree
from tornado.options import define

import slickbird.orm as orm
from slickbird import filenames


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

    def __init__(self, session, home, name, directory, filename, dat):
        self.session = session
        self.home = home
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
        base = pj(self.home, self.directory)
        mkdir_p(base)
        mkdir_p(pj(base, 'artwork'))
        mkdir_p(pj(base, 'nfos'))
        nfofile = pj(base, 'omniitem.nfo')
        if not os.path.exists(nfofile):
            nfo = etree.Element('omniitem')
            etree.SubElement(nfo, 'title').text = self.name
            target = etree.SubElement(nfo, 'target')
            target.text = 'nfos/*.nfo'
            target.attrib['type'] = 'glob'
            etree.ElementTree(nfo).write(
                nfofile,
                encoding='utf-8', xml_declaration=True, pretty_print=True)
        _log().info('collection {} is now ready'.format(self.cdb.name))
        self.cdb.status = 'ready'
        self.session.commit()


class FileImporter(object):

    def __init__(self, session, home):
        self.session = session
        self.home = home

    def file_import(self, filepath):
        try:
            with open(filepath, mode='rb') as fd:
                crc = binascii.crc32(fd.read()) & 0xffffffff
            fcrc = '%08X' % crc
        except Exception as e:
            return False, 'error: ' + str(e)
        status = 'irrelevant'
        for r in self.session.query(orm.Rom)\
                .filter(orm.Rom.crc == fcrc):
            v = r.variant
            dst = filenames.variant(self.home, v)
            mkdir_p(os.path.dirname(dst))
            shutil.copyfile(filepath, dst)
            status = 'moved'
            _log().info('mv {} {}'.format(filepath, dst))
            v.game.status = 'ok'
        if status == 'moved':
            os.unlink(filepath)
        self.session.commit()
        return True, status
