'''Slickbird scanner handler'''

import os
import logging
import json
import errno

import tornado.gen
import tornado.ioloop
import tornado.web
from tornado.locks import Condition
from tornado.web import URLSpec

from slickbird.web import hbase
import slickbird
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

    def __init__(self, session, home, scrapper):
        self.session = session
        self.home = home
        self.condition = Condition()
        self.scrapper = scrapper
        tornado.ioloop.IOLoop.current()\
            .spawn_callback(self.main)

    @tornado.gen.coroutine
    def main(self):
        _log().info('scanner sleeping')
        yield self.condition.wait()
        _log().info('scanner woke up')
        changed = True
        while changed:
            changed = yield self.work()
        tornado.ioloop.IOLoop.current()\
            .spawn_callback(self.main)

    @tornado.gen.coroutine
    def work(self):
        changed = False
        fi = slickbird.FileImporter(self.session, self.home)
        for f in self.session.query(orm.Scannerfile)\
                .filter(orm.Scannerfile.status == 'scanning'):
            changed = True
            r, status = fi.file_import(f.filename)
            f.status = status
            if status == 'moved':
                self.scrapper.condition.notify()
            yield tornado.gen.moment
        self.session.commit()
        self.scrapper.condition.notify()
        raise tornado.gen.Return(changed)


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


class ScannerClearHandler(tornado.web.RequestHandler):

    def post(self):
        _log().info('clearning scanner data')
        self.settings['session'].query(orm.Scannerfile).delete()
        self.settings['session'].commit()
        self.write(json.dumps({'result': True}))


# Install: ###################################################################

def install(app):
    w = ScannerWorker(app.settings['session'],
                      app.settings['home'],
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
        URLSpec(r'/api/scanner_clear',
                ScannerClearHandler,
                name='api_scanner_clear'),
    ])
