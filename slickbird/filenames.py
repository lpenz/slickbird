'''Functions that generate filenames'''

import os


pjoin = os.path.join


def vdir(home, variant):
    return pjoin(home,
                 variant.game.collection.directory,
                 variant.game.name,
                 )


def variant(home, variant):
    d = vdir(home, variant)
    if len(variant.roms) == 1:
        rv = pjoin(d, variant.roms[0].filename)
    else:
        rv = pjoin(d, variant.name)
    return rv


def nfo(home, variant):
    return pjoin(
        vdir(home, variant),
        'omniitem.nfo')
