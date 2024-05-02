:py:mod:`sxdm.widgets.bliss.Inspect4DSXDM`
==========================================

.. py:module:: sxdm.widgets.bliss.Inspect4DSXDM

.. autodoc2-docstring:: sxdm.widgets.bliss.Inspect4DSXDM
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`Inspect4DSXDM <sxdm.widgets.bliss.Inspect4DSXDM.Inspect4DSXDM>`
     - .. autodoc2-docstring:: sxdm.widgets.bliss.Inspect4DSXDM.Inspect4DSXDM
          :summary:

Data
~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`_det_aliases <sxdm.widgets.bliss.Inspect4DSXDM._det_aliases>`
     - .. autodoc2-docstring:: sxdm.widgets.bliss.Inspect4DSXDM._det_aliases
          :summary:

API
~~~

.. py:data:: _det_aliases
   :canonical: sxdm.widgets.bliss.Inspect4DSXDM._det_aliases
   :value: 'dict(...)'

   .. autodoc2-docstring:: sxdm.widgets.bliss.Inspect4DSXDM._det_aliases

.. py:class:: Inspect4DSXDM(path_dset, scan_no, detector=None)
   :canonical: sxdm.widgets.bliss.Inspect4DSXDM.Inspect4DSXDM

   Bases: :py:obj:`sxdm.widgets.Inspect4DArray`

   .. autodoc2-docstring:: sxdm.widgets.bliss.Inspect4DSXDM.Inspect4DSXDM

   .. rubric:: Initialization

   .. autodoc2-docstring:: sxdm.widgets.bliss.Inspect4DSXDM.Inspect4DSXDM.__init__

   .. py:method:: _custom_roi_callback(eclick, erelease)
      :canonical: sxdm.widgets.bliss.Inspect4DSXDM.Inspect4DSXDM._custom_roi_callback

      .. autodoc2-docstring:: sxdm.widgets.bliss.Inspect4DSXDM.Inspect4DSXDM._custom_roi_callback

   .. py:method:: _onclick_callback(event)
      :canonical: sxdm.widgets.bliss.Inspect4DSXDM.Inspect4DSXDM._onclick_callback

      .. autodoc2-docstring:: sxdm.widgets.bliss.Inspect4DSXDM.Inspect4DSXDM._onclick_callback

   .. py:method:: _update_plots()
      :canonical: sxdm.widgets.bliss.Inspect4DSXDM.Inspect4DSXDM._update_plots

      .. autodoc2-docstring:: sxdm.widgets.bliss.Inspect4DSXDM.Inspect4DSXDM._update_plots

   .. py:method:: _add_rois(change)
      :canonical: sxdm.widgets.bliss.Inspect4DSXDM.Inspect4DSXDM._add_rois

      .. autodoc2-docstring:: sxdm.widgets.bliss.Inspect4DSXDM.Inspect4DSXDM._add_rois
