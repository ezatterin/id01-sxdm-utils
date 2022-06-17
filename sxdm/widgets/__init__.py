import matplotlib as mpl

mpl.rcParams['keymap.back'].remove('left')
mpl.rcParams['keymap.forward'].remove('right')

from . import (bliss, spec, xsocs)
