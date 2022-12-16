import matplotlib as mpl

from . import bliss

try:
    mpl.rcParams['keymap.back'].remove('left')
    mpl.rcParams['keymap.forward'].remove('right')
except ValueError:
    pass

from . import (spec, xsocs)
from .Inspect4DArray import Inspect4DArray
