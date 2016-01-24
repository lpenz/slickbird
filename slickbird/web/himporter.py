'''Slickbird importer handler'''

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


# Importer worker coroutine: #################################################

class ImporterWorker(object):

    def __init__(self, session, home, scrapper):
        self.session = session
        self.home = home
        self.condition = Condition()
        self.scrapper = scrapper
        tornado.ioloop.IOLoop.current()\
            .spawn_callback(self.main)

    @tornado.gen.coroutine
    def main(self):
        _log().info('importer sleeping')
        yield self.condition.wait()
        _log().info('importer woke up')
        changed = True
        while changed:
            changed = yield self.work()
        tornado.ioloop.IOLoop.current()\
            .spawn_callback(self.main)

    @tornado.gen.coroutine
    def work(self):
        changed = False
        fi = slickbird.FileImporter(self.session, self.home)
        for f in self.session.query(orm.Importerfile)\
                .filter(orm.Importerfile.status == 'scanning'):
            changed = True
            r, status = fi.file_import(f.filename)
            f.status = status
            if status == 'moved':
                self.scrapper.condition.notify()
            yield tornado.gen.moment
        self.session.commit()
        self.scrapper.condition.notify()
        raise tornado.gen.Return(changed)


# Importer handler: ###########################################################

class ImporterAddHandler(hbase.PageHandler):
    name = 'importer_add'

    def initialize(self, worker):
        self.worker = worker

    @tornado.gen.coroutine
    def importer(self, directory):
        for root, dirs, files in os.walk(directory):
            for f in files:
                _log().debug('queue directory {} file {}'
                             .format(directory, f))
                fdb = orm.Importerfile(
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
        self.redirect(self.reverse_url('importer_lst'))
        tornado.ioloop.IOLoop.current()\
            .spawn_callback(self.importer, directory)


# API: #######################################################################

class ImporterDataHandler(tornado.web.RequestHandler):

    def get(self):
        fdb = self.settings['session'].query(orm.Importerfile)
        fs = [f.as_dict() for f in fdb]
        _log().debug('returning {} files'
                     .format(len(fs)))
        self.write(json.dumps(fs))


class ImporterClearHandler(tornado.web.RequestHandler):

    def post(self):
        _log().info('clearning importer data')
        self.settings['session'].query(orm.Importerfile).delete()
        self.settings['session'].commit()
        self.write(json.dumps({'result': True}))


# Install: ###################################################################

def install(app):
    w = ImporterWorker(app.settings['session'],
                       app.settings['home'],
                       app.settings['scrapper'])
    app.add_handlers('.*', [
        # Importer:
        URLSpec(r'/importer/add',
                ImporterAddHandler,
                dict(worker=w),
                name='importer_add'),
        URLSpec(r'/importer/list',
                hbase.genPageHandler('importer_lst'),
                name='importer_lst'),
        URLSpec(r'/api/importer_lst.json',
                ImporterDataHandler,
                name='api_importer_lst'),
        URLSpec(r'/api/importer_clear',
                ImporterClearHandler,
                name='api_importer_clear'),
    ])
