:py:mod:`sxdm.plot.utils`
=========================

.. py:module:: sxdm.plot.utils

.. autodoc2-docstring:: sxdm.plot.utils
   :allowtitles:

Module Contents
---------------

Functions
~~~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`add_scalebar <sxdm.plot.utils.add_scalebar>`
     - .. autodoc2-docstring:: sxdm.plot.utils.add_scalebar
          :summary:
   * - :py:obj:`add_colorbar <sxdm.plot.utils.add_colorbar>`
     - .. autodoc2-docstring:: sxdm.plot.utils.add_colorbar
          :summary:
   * - :py:obj:`add_directions <sxdm.plot.utils.add_directions>`
     - .. autodoc2-docstring:: sxdm.plot.utils.add_directions
          :summary:
   * - :py:obj:`gif_sxdm_sums <sxdm.plot.utils.gif_sxdm_sums>`
     - .. autodoc2-docstring:: sxdm.plot.utils.gif_sxdm_sums
          :summary:
   * - :py:obj:`gif_sxdm <sxdm.plot.utils.gif_sxdm>`
     - .. autodoc2-docstring:: sxdm.plot.utils.gif_sxdm
          :summary:

API
~~~

.. py:function:: add_scalebar(ax, h_size=None, v_size=None, label=None, color='black', loc='lower right', pad=0.5, sep=5, **font_kwargs)
   :canonical: sxdm.plot.utils.add_scalebar

   .. autodoc2-docstring:: sxdm.plot.utils.add_scalebar

.. py:function:: add_colorbar(ax, mappable, loc='right', size='3%', pad=0.05, label_size='small', scientific_notation=False, **kwargs)
   :canonical: sxdm.plot.utils.add_colorbar

   .. autodoc2-docstring:: sxdm.plot.utils.add_colorbar

.. py:function:: add_directions(ax, text_x, text_y, loc='lower left', color='k', transform=None, angle=0, length=0.1, line_width=0.5, aspect_ratio=1, head_width=1.2, head_length=3, arrow_props=None, tpad_x=0.01, tpad_y=0.01, text_props=None, pad=0.4, borderpad=0.5, frameon=False, return_artist=False)
   :canonical: sxdm.plot.utils.add_directions

   .. autodoc2-docstring:: sxdm.plot.utils.add_directions

.. py:function:: gif_sxdm_sums(path_dset, scan_nos, gif_duration=5, moving_motor='eta', clim_sample=[None, None], clim_detector=[None, None], detector=None)
   :canonical: sxdm.plot.utils.gif_sxdm_sums

   .. autodoc2-docstring:: sxdm.plot.utils.gif_sxdm_sums

.. py:function:: gif_sxdm(path_dset, detector_roi=None, scan_nos=None, gif_duration=5, moving_motor='eta', clim_sample=[None, None], detector=None)
   :canonical: sxdm.plot.utils.gif_sxdm

   .. autodoc2-docstring:: sxdm.plot.utils.gif_sxdm
