'''Slickbird scrapper'''

import logging
import os
import re
import io
import tornado.gen
import tornado.escape
import tornado.httpclient

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote
from lxml import etree

import slickbird.orm as orm
from slickbird import filenames

pjoin = os.path.join


def _log():
    if not _log.logger:
        _log.logger = logging.getLogger(__name__)
    return _log.logger
_log.logger = None


# Scrapper: ##################################################################

class Scrapper(object):
    FIELDMAP = {
        'title': './GameTitle',
        'year': './ReleaseDate',
        'publisher': './Publisher',
        'platform': './Platform',
        'genre': './Genres/genre',
        'plot': './Overview',
    }

    def __init__(self, session, home):
        self.session = session
        self.home = home

    @tornado.gen.coroutine
    def scrap_missing(self):
        l = []
        for v in self.session.query(orm.Variant):
            nfofile = filenames.nfo(self.home,
                                    v)
            if os.path.exists(nfofile):
                _log().debug('scrapper skipping {}, found {}'
                             .format(v.name, nfofile))
                continue
            l.append(self.scrap(v, nfofile))
            if len(l) > 5:
                yield l
                l = []
        if len(l) > 0:
            yield l

    @tornado.gen.coroutine
    def scrap(self, v, nfofile):
        _log().info('scrapping {}'.format(v.name))
        url = 'http://thegamesdb.net/api/GetGame.php?exactname=' + \
            quote(v.game.name)
        http = tornado.httpclient.AsyncHTTPClient()
        response = yield http.fetch(url)
        if response.code != 200:
            _log().warn('error scrapping {}: {}'
                        .format(v.game.name, str(response)))
            raise tornado.gen.Return()
        try:
            etr = etree.fromstring(response.body)
        except Exception as e:
            _log().warn('scrapping error in {}, got invalid XML ({})'
                        .format(v.name, str(e)))
        nfo = {}
        for g in etr.findall('./Game'):
            for f, xpath in self.FIELDMAP.items():
                e = g.find(xpath)
                if e is not None:
                    nfo[f] = e.text
            if 'year' in nfo and nfo['year'] is not None:
                nfo['year'] = re.sub(
                    '.*([0-9]{4})$', '\\1', nfo['year'])
        etw = etree.Element('game')
        for f in self.FIELDMAP.keys():
            if f in nfo:
                etree.SubElement(etw, f).text = nfo[f]
        etwstr = etree.tostring(etw,
                                pretty_print=True)
        with io.open(nfofile, 'w') as fd:
            fd.write(etwstr.decode('utf-8'))
        v.game.nfostatus = 'present'
        _log().info('scrapped {}'.format(nfofile))
        self.session.commit()
        raise tornado.gen.Return(None)
