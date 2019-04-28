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
        lines = []
        for v in self.session.query(orm.Variant):
            nfofile = filenames.nfo(self.home,
                                    v)
            if os.path.exists(nfofile):
                _log().debug('scrapper skipping {}, found {}'
                             .format(v.name, nfofile))
                continue
            romfile = filenames.variant(self.home, v)
            if not os.path.exists(romfile):
                _log().debug('scrapper skipping {}, rom not found {}'
                             .format(v.name, romfile))
                continue
            lines.append(self.scrap(v, nfofile))
            if len(lines) > 5:
                try:
                    yield lines
                except Exception as e:
                    _log().warn('scrapping error ({}), skip'.format(str(e)))
                lines = []
        if len(lines) > 0:
            yield lines

    @tornado.gen.coroutine
    def scrap(self, v, nfofile):
        _log().info('scrapping {}'.format(v.name))
        url = 'http://thegamesdb.net/api/GetGame.php?exactname=' + \
            quote(v.game.name)
        http = tornado.httpclient.AsyncHTTPClient()
        try:
            response = yield http.fetch(url)
        except Exception as e:
            _log().warn('error scrapping {}: {}'
                        .format(v.name, str(e)))
            raise tornado.gen.Return(None)
        if response.code != 200:
            _log().warn('error scrapping {}: {}'
                        .format(v.game.name, str(response)))
            raise tornado.gen.Return()
        try:
            etr = etree.fromstring(response.body)
        except Exception as e:
            _log().warn('scrapping error in {}, got invalid XML ({})'
                        .format(v.name, str(e)))
        nfodir = os.path.dirname(nfofile)
        if not os.path.exists(nfodir):
            os.makedirs(nfodir)
        nfo = {}
        baseimageurl = etr.find('./baseImgUrl').text
        images = {}
        imagesyield = []
        for g in etr.findall('./Game'):
            for f, xpath in self.FIELDMAP.items():
                e = g.find(xpath)
                if e is not None:
                    nfo[f] = e.text
            if 'year' in nfo and nfo['year'] is not None:
                nfo['year'] = re.sub(
                    '.*([0-9]{4})$', '\\1', nfo['year'])
            for img in g.findall('./Images/*'):
                if img.tag in images:
                    continue
                if img.tag == 'boxart' \
                   and img.attrib.get('side', '') == 'back':
                    continue
                imgo = img.find('./original')
                if imgo is not None:
                    base = imgo.text
                else:
                    base = img.text
                filename = base.replace('/', '_')
                images[img.tag] = filename
                url = os.path.join(baseimageurl, base)
                imagesyield.append(
                    self.image_fetch(v, nfodir, img.tag, url, filename))
        yield imagesyield
        etw = etree.Element('omniitem')
        etree.SubElement(etw, 'title').text = v.game.name
        eti = etree.SubElement(etw, 'info')
        for f in self.FIELDMAP.keys():
            if f in nfo:
                etree.SubElement(eti, f).text = nfo[f]
        eta = etree.SubElement(etw, 'art')
        for art, filename in images.items():
            etree.SubElement(eta, art).text = filename
        for missing, alts in {
            'fanart': ['banner', 'screenshot'],
            'icon': ['boxart', 'clearlogo', 'thumb'],
            'thumb': ['boxart', 'clearlogo', 'icon'],
        }.items():
            if missing in images:
                continue
            for a in alts:
                if a not in images:
                    continue
                etree.SubElement(eta, missing)\
                    .text = images[a]
                break
        ett = etree.SubElement(etw, 'target')
        ett.attrib['type'] = 'command'
        ett.text = 'echo 1'
        etwstr = etree.tostring(etw,
                                pretty_print=True)
        with io.open(nfofile, 'w') as fd:
            fd.write(etwstr.decode('utf-8'))
        v.game.nfostatus = 'present'
        _log().info('scrapped {} for {}'.format(nfofile, v.game.name))
        self.session.commit()
        raise tornado.gen.Return(None)

    @tornado.gen.coroutine
    def image_fetch(self, v, nfodir, tag, url, filename):
        http = tornado.httpclient.AsyncHTTPClient()
        try:
            response = yield http.fetch(url)
        except Exception as e:
            _log().warn('error scrapping {} of {}: {}'
                        .format(tag, v.name, str(e)))
            raise tornado.gen.Return(None)
        with io.open(os.path.join(nfodir, filename), 'wb') as fd:
            fd.write(response.body)
