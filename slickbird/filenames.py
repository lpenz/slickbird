'''Functions that generate filenames'''

import os
import re

pjoin = os.path.join


def rom(deploydir, rom):
    return pjoin(deploydir,
                 rom.game.collection.name,
                 rom.filename)


def nfo(deploydir, rom):
    return re.sub('\.[^.]+$',
                  '.nfo',
                  pjoin(deploydir,
                        rom.game.collection.name,
                        rom.filename))
