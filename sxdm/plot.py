"""
Helper functions useful to plot SXDM maps.
"""

import numpy as np

import matplotlib.font_manager as fm
import matplotlib as mpl
import matplotlib.pyplot as plt

from mpl_toolkits.axes_grid1 import make_axes_locatable, anchored_artists
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar, AnchoredDirectionArrows
from matplotlib.patches import FancyArrowPatch, Rectangle, Circle

def make_hsv(tiltmag, azimuth, stretch=False):

    # hue is the azimuth - normalised [0,1] - needed for HSV
    h = (azimuth % 360) / (360) 

    # saturation is the tilt - normalised [0,1]
    s = np.abs(tiltmag)
    if stretch:
        s -= s.min()
    s /= s.max()

    # value is just 1
    v = np.ones_like(h)

    # stack the array
    im = np.dstack((h,v,s))
    im = mpl.colors.hsv_to_rgb(im)

    return im

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

# TODO - change with anchored dir arrows or auto ax calc
def add_directions(ax, up, right, x=0.07, y=0.07, labelpadx=0.12, labelpady=0.12, alx=0.1, aly=0.1, hw=1.2, hl=3, fs='small', custom=False, **kwargs):

    arr = FancyArrowPatch((x,y), (x, y+aly), transform=ax.transAxes,
                          arrowstyle='->, head_width={}, head_length={}'.format(hw,hl), linewidth=0.5, shrinkA=0.0, shrinkB=0.0, **kwargs)
    arr2 = FancyArrowPatch((x,y), (x+alx, y), transform=ax.transAxes,
                          arrowstyle='->, head_width={}, head_length={}'.format(hw,hl), linewidth=0.5, shrinkA=0.0, shrinkB=0.0, **kwargs)
    ax.add_patch(arr)
    ax.add_patch(arr2)

    if custom:
        txt_up = up
        txt_right = right
    else:
        txt_up = r'$\;\;[{}]$'.format(up)
        txt_right = r'$[{}]$'.format(right)

    ax.text(x, y+aly+labelpady, txt_up, ha='center', va='bottom', transform=ax.transAxes, fontsize=fs, **kwargs)
    ax.text(x+alx+labelpadx, y, txt_right, ha='left', va='center', transform=ax.transAxes, fontsize=fs, **kwargs)
