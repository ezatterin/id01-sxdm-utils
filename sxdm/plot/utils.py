"""
Helper functions useful to plot SXDM maps.
"""


import numpy as np
import matplotlib.font_manager as fm
import matplotlib as mpl

from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar

from matplotlib.patches import FancyArrowPatch, Rectangle, ArrowStyle
from matplotlib.offsetbox import AuxTransformBox


def add_hsv_colorbar(tiltmag, ax, labels, size="20%", pad=0.05):
    a, b = np.meshgrid(np.linspace(0, 1, 100), np.linspace(180, -180, 100))
    cmap = make_hsv(a, b)

    cax = make_axes_locatable(ax).append_axes("right", size=size, pad=pad)
    cax.imshow(cmap, aspect="auto")

    cax.tick_params(
        labelsize="small", left=False, right=True, labelleft=False, labelright=True
    )
    cax.locator_params(axis="y", tight=True, nbins=7)

    cax.set_yticks([0, 25, 50, 75, 100])
    cax.set_yticklabels(labels)

    cax.set_xticks([0, 99])
    cax.set_xticklabels([f"{tiltmag.min():.2f}", f"{tiltmag.max():.2f}"], rotation=40)

    cax.yaxis.set_label_position("right")
    cax.set_ylabel(r"Direction", labelpad=3, fontsize="small")
    cax.set_xlabel(r"Magnitude $(\degree)$", labelpad=1, fontsize="small")

    return cax


def make_hsv(tiltmag, azimuth, stretch=False, v2s=False):

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
    if v2s:
        im = np.dstack((h, v, s))
    else:
        im = np.dstack((h, s, v))
    im = mpl.colors.hsv_to_rgb(im)

    return im


def add_scalebar(
    ax,
    x_scale=3,
    y_scale=100,
    label=None,
    color="black",
    loc="lower right",
    pad=0.5,
    sep=5,
    **font_kwargs,
):

    # size of the img in data coords
    try:
        img = ax.get_images()[0]
        ext = img.get_extent()  # left, right, bottom, top
        xsize, ysize = (ext[1] - ext[0], ext[3] - ext[2])
    except AttributeError:
        img = [x for x in ax.get_children() if type(x) == mpl.collections.QuadMesh][0]
        xc, yc = img.get_coordinates().T
        xsize, ysize = [c.max() - c.min() for c in (xc, yc)]

    # size of the scalebar wrt the image size in um or nm
    h_size = xsize / x_scale
    v_size = ysize / y_scale

    # label
    if label is None:
        label = f"{h_size:.3f}"

    # the scale bar object
    fontprops = fm.FontProperties(**font_kwargs)
    scalebar = AnchoredSizeBar(
        ax.transData,
        h_size,
        label,
        loc,
        color=color,
        frameon=False,
        size_vertical=v_size,
        pad=pad,
        sep=sep,
        fontproperties=fontprops,
    )

    # add scalebar to ax
    ax.add_artist(scalebar)


def add_colorbar(
    ax, mappable, loc="right", size="3%", pad=0.05, label_size="small", **kwargs
):

    fig = ax.get_figure()
    cax = make_axes_locatable(ax).append_axes(loc, size=size, pad=pad)
    cax.tick_params(labelsize=label_size)
    cbar = fig.colorbar(mappable, cax=cax, **kwargs)

    return cbar


def add_roi_box(ax, roi, **kwargs):
    rect = Rectangle((roi[0], roi[2]), roi[1] - roi[0], roi[3] - roi[2], **kwargs)
    ax.add_patch(rect)


def add_letter(ax, letter, x=0.03, y=0.92, fs="large", fw="bold", **kwargs):

    txt = ax.text(
        x, y, letter, transform=ax.transAxes, fontweight=fw, fontsize=fs, **kwargs
    )
    return txt


def add_roilabel(ax, roi):
    at = mpl.offsetbox.AnchoredText(
        "{}".format(roi),
        loc="upper left",
        frameon=False,
        pad=0.05,
        prop=dict(
            color="black",
            fontsize="small",
            bbox=dict(facecolor="whitesmoke", alpha=0.7, lw=0, pad=1.5),
        ),
    )
    ax.add_artist(at)


def add_directions(
    ax,
    text_x,
    text_y,
    loc,
    color="k",
    transform=None,
    angle=0,
    length=0.1,
    line_width=0.5,
    aspect_ratio=1,
    head_width=1.2,
    head_length=3,
    arrow_props=None,
    tpad_x=0.01,
    tpad_y=0.01,
    text_props=None,
    pad=0.4,
    borderpad=0.5,
    frameon=False,
    **obox_kwargs,
):

    ## arrows

    alx = length
    aly = length * aspect_ratio

    arrowstyle = ArrowStyle("->", head_width=head_width, head_length=head_length)
    if arrow_props is None:
        arrow_props = dict()
    if "color" not in arrow_props:
        arrow_props["color"] = color
    if "linewidth" not in arrow_props:
        arrow_props["linewidth"] = line_width

    a_coords = [(0, aly), (alx, 0)]
    arr_x, arr_y = [
        FancyArrowPatch(
            (0, 0),
            c,
            arrowstyle=arrowstyle,
            shrinkA=0.0,
            shrinkB=0.0,
            **arrow_props,
        )
        for c in a_coords
    ]

    ## text

    if text_props is None:
        text_props = dict()
    if "color" not in text_props:
        text_props["color"] = color

    t_coords = [((alx + tpad_x), 0), (0, (aly + tpad_y))]
    t_align = [dict(va="center"), dict(ha="center")]

    txt_x, txt_y = [
        mpl.text.Text(
            *c,
            t,
            transform=transform,
            **al,
            **text_props,
        )
        for c, t, al in zip(t_coords, [text_x, text_y], t_align)
    ]

    ## box

    if transform is None:
        transform = ax.transAxes

    t_start = transform
    t_end = t_start + mpl.transforms.Affine2D().rotate_deg(angle)

    box = mpl.offsetbox.AuxTransformBox(t_end)
    [box.add_artist(a) for a in (arr_x, arr_y, txt_x, txt_y)]

    ## anchored box

    abox = mpl.offsetbox.AnchoredOffsetbox(
        loc, child=box, pad=pad, borderpad=borderpad, frameon=frameon, **obox_kwargs
    )

    ax.add_artist(abox)
