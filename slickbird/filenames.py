'''Functions that generate filenames'''

import os
import re

pjoin = os.path.join


def variant(home, variant):
    d = pjoin(home, variant.game.collection.directory)
    if len(variant.roms) == 1:
        rv = pjoin(d, variant.roms[0].filename)
    else:
        rv = pjoin(d, variant.name)
    return rv


def nfo(home, v):
    return re.sub('\.[^.]+$',
                  '.nfo',
                  variant(home, v))
