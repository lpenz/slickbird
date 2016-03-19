'''Functions that generate filenames'''

import os


pjoin = os.path.join


def variant(home, variant):
    d = pjoin(
        home,
        variant.game.collection.directory,
        'roms',
        variant.game.name)
    if len(variant.roms) == 1:
        rv = pjoin(d, variant.roms[0].filename)
    else:
        rv = pjoin(d, variant.name)
    return rv


def nfo(home, variant):
    d = pjoin(
        home,
        variant.game.collection.directory,
        'meta',
        variant.game.name,
        'omniitem.nfo')
    return d
