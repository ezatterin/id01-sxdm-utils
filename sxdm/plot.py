"""
Helper functions useful to plot SXDM maps.
"""

import matplotlib.font_manager as fm
import matplotlib as mpl
import matplotlib.pyplot as plt

from mpl_toolkits.axes_grid1 import make_axes_locatable, anchored_artists
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar, AnchoredDirectionArrows
from matplotlib.patches import FancyArrowPatch, Rectangle, Circle

def add_scalebar(ax, xsize, unit, h_scale=5, v_scale=150,
                font_size='small', label='auto', color='black',
                 loc='lower right', pad=0.5, sep=5, **kwargs):

    # size of the image within ax in pixels
    try:
        img = ax.get_images()[0]
        ypix, xpix = img.get_size()
    except:
        img = [x for x in ax.get_children() if type(x) == mpl.collections.QuadMesh][0]
        ypix, xpix = img._meshHeight+1, img._meshWidth+1

    # size of the scalebar wrt the image size in um or nm
    h_size = xsize/h_scale
    v_size = xsize/v_scale

    # the scale bar object
    fontprops = fm.FontProperties(size=font_size)

    scalebarlabel = '{0:.3f} {1}'.format(h_size, unit)
    if label != 'auto':
        scalebarlabel = label

    scalebar = AnchoredSizeBar(ax.transData, h_size, scalebarlabel, loc,
                               color=color, frameon=False, size_vertical=v_size, pad=pad,
                               sep=sep, fontproperties=fontprops, **kwargs)

    # add scalebar to ax
    ax.add_artist(scalebar)

def add_colorbar(ax, mappable, loc='right', size='3%', pad=0.05, label_size='small', **kwargs):

    fig = ax.get_figure()
    cax = make_axes_locatable(ax).append_axes(loc, size=size, pad=pad)
    cax.tick_params(labelsize=label_size)
    cbar = fig.colorbar(mappable, cax=cax, **kwargs)

    return cbar

def add_roi_box(ax, roi, **kwargs):
    rect = Rectangle((roi[0], roi[2]), roi[1]-roi[0], roi[3]-roi[2], **kwargs)
    ax.add_patch(rect)

def add_letter(ax, letter, x=0.03, y=0.92, fs='large', fw='bold', **kwargs):

    txt = ax.text(x, y, letter, transform=ax.transAxes, fontweight=fw, fontsize=fs, **kwargs)
    return txt

def add_roilabel(ax, roi):
    at = mpl.offsetbox.AnchoredText('{}'.format(roi), loc='upper left', frameon=False, pad=.05, 
                                    prop=dict(color='black', fontsize='small',  
                                    bbox=dict(facecolor='whitesmoke', alpha=0.7, lw=0, pad=1.5)))
    ax.add_artist(at)
