import matplotlib as mpl

try:
    mpl.rcParams['keymap.back'].remove('left')
    mpl.rcParams['keymap.forward'].remove('right')
except ValueError:
    pass

from . import (bliss, spec, xsocs)
