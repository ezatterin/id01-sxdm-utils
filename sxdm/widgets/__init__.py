import matplotlib as mpl

from .Inspect4DArray import Inspect4DArray
from . import bliss

try:
    mpl.rcParams["keymap.back"].remove("left")
    mpl.rcParams["keymap.forward"].remove("right")
except ValueError:
    pass

from . import spec, xsocs
