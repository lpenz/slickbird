'''Slickbird scanner handler'''

import os
import logging
import json
import hashlib
import shutil
import errno

import tornado.gen
import tornado.ioloop
import tornado.web
from tornado.locks import Condition
from tornado.web import URLSpec

from slickbird import hbase
import slickbird.orm as orm


pjoin = os.path.join


def _log():
    if not _log.logger:
        _log.logger = logging.getLogger(__name__)
    return _log.logger
_log.logger = None


# Utility functions: #########################################################

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


# Scanner worker coroutine: ##################################################

class ScannerWorker(object):

    def __init__(self, session, deploydir, scrapper):
        self.session = session
        self.deploydir = deploydir
        self.condition = Condition()
        self.scrapper = scrapper
        tornado.ioloop.IOLoop.current()\
            .spawn_callback(self.work)

    @tornado.gen.coroutine
    def work(self):
        _log().info('scanner sleeping')
        yield self.condition.wait()
        _log().info('scanner woke up')
        changed = True
        while changed:
            changed = False
            for f in self.session.query(orm.Scannerfile)\
                    .filter(orm.Scannerfile.status == 'scanning'):
                changed = True
                try:
                    m = hashlib.md5()
                    m.update(open(f.filename, mode='rb').read())
                    fmd5 = m.hexdigest().upper()
                except Exception as e:
                    f.status = 'error: ' + str(e)
                    continue
                for r in self.session.query(orm.Rom)\
                        .filter(orm.Rom.md5 == fmd5):
                    dstd = pjoin(self.deploydir,
                                 r.game.collection.name)
                    mkdir_p(dstd)
                    dst = pjoin(dstd, r.filename)
                    shutil.copyfile(f.filename, dst)
                    f.status = 'moved'
                    _log().info('mv {} {}'.format(f.filename, dst))
                    r.local = dst
                    r.game.status = 'ok'
                if f.status == 'moved':
                    os.unlink(f.filename)
                    self.scrapper.condition.notify()
                else:
                    f.status = 'irrelevant'
                yield tornado.gen.moment
        self.scrapper.condition.notify()
        self.session.commit()
        tornado.ioloop.IOLoop.current()\
            .spawn_callback(self.work)


# Scanner handler: ###########################################################

class ScannerAddHandler(hbase.PageHandler):
    name = 'scanner_add'

    def initialize(self, worker):
        self.worker = worker

    @tornado.gen.coroutine
    def scanner(self, directory):
        for root, dirs, files in os.walk(directory):
            for f in files:
                _log().debug('queue directory {} file {}'
                             .format(directory, f))
                fdb = orm.Scannerfile(
                    filename=os.path.join(root, f),
                    status='scanning',
                )
                self.settings['session'].add(fdb)
                yield tornado.gen.moment
        self.settings['session'].commit()
        self.worker.condition.notify()

    @tornado.gen.coroutine
    def post(self):
        directory = self.get_argument('directory')
        self.redirect(self.reverse_url('scanner_lst'))
        tornado.ioloop.IOLoop.current()\
            .spawn_callback(self.scanner, directory)


# API: #######################################################################

class ScannerDataHandler(tornado.web.RequestHandler):

    def get(self):
        fdb = self.settings['session'].query(orm.Scannerfile)
        fs = [f.as_dict() for f in fdb]
        _log().debug('returning {} files'
                     .format(len(fs)))
        self.write(json.dumps(fs))


# Install: ###################################################################

def install(app):
    w = ScannerWorker(app.settings['session'],
                      app.settings['deploydir'],
                      app.settings['scrapper'])
    app.add_handlers('.*', [
        # Scanner:
        URLSpec(r'/scanner/add',
                ScannerAddHandler,
                dict(worker=w),
                name='scanner_add'),
        URLSpec(r'/scanner/list',
                hbase.genPageHandler('scanner_lst'),
                name='scanner_lst'),
        URLSpec(r'/api/scanner_lst.json',
                ScannerDataHandler,
                name='api_scanner_lst'),
    ])
