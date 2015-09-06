import re

from StringIO import StringIO

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
            fd = open(filename)
        if datstr is not None:
            fd = StringIO(datstr)
    assert fd
    et = etree.parse(fd)
    d = {}
    for e in et.iterfind('/game'):
        name = nameclean(e.attrib.get('cloneof', e.attrib['name']))
        d.setdefault(name, [])
        n = {
            'name': e.attrib.get('cloneof', e.attrib['name']),
            'description': e.find('description').text,
            'releases': [r.attrib for r in e.iterfind('release')],
            'rom': e.find('rom').attrib,
        }
        if 'cloneof' in e.attrib:
            n['cloneof'] = e.attrib['cloneof']
        d[name].append(n)
    return OrderedDict(sorted(d.items(), key=lambda t: t[0]))
