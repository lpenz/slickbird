'''.dat XML from NO-INTRO parser'''

import re

import io

from lxml import etree

from collections import OrderedDict


def nameclean(name0):
    r = re.compile(r'''(.*)\s\([^)]+\)$''')
    n = name0
    while True:
        m = r.match(n)
        if not m:
            return n
        n = m.group(1)


def parse(fd=None, filename=None, datstr=None):
    if fd is None:
        if filename is not None:
            fd = io.open(filename, encoding='utf-8')
        if datstr is not None:
            fd = io.StringIO(datstr)
    assert fd
    et = etree.parse(fd)
    fd.close()
    games = {}
    for e in et.iterfind('/game'):
        name = nameclean(e.attrib.get('cloneof', e.attrib['name']))
        g = games.setdefault(name, {'name': name, 'variants': []})
        v = {
            'name': e.attrib.get('cloneof', e.attrib['name']),
            'description': e.find('description').text,
            'releases': [r.attrib for r in e.iterfind('release')],
            'roms': [{
                'filename': e.find('rom').attrib['name'],
                'size': e.find('rom').attrib['size'],
                'crc': e.find('rom').attrib['crc'],
            }],
        }
        if 'cloneof' in e.attrib:
            v['cloneof'] = e.attrib['cloneof']
        g['variants'].append(v)
    return {
        'header': dict(((e.tag, e.text) for e in et.find('/header').iter())),
        'games': OrderedDict(sorted(games.items(), key=lambda t: t[0])),
    }
