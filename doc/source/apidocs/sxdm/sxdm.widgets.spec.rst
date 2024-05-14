:py:mod:`sxdm.widgets.spec`
===========================

.. py:module:: sxdm.widgets.spec

.. autodoc2-docstring:: sxdm.widgets.spec
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`RoiPlotter <sxdm.widgets.spec.RoiPlotter>`
     - .. autodoc2-docstring:: sxdm.widgets.spec.RoiPlotter
          :summary:
   * - :py:obj:`FramesExplorer <sxdm.widgets.spec.FramesExplorer>`
     - .. autodoc2-docstring:: sxdm.widgets.spec.FramesExplorer
          :summary:

API
~~~

.. py:class:: RoiPlotter(fast_spec_file, detector='maxipix')
   :canonical: sxdm.widgets.spec.RoiPlotter

   Bases: :py:obj:`object`

   .. autodoc2-docstring:: sxdm.widgets.spec.RoiPlotter

   .. rubric:: Initialization

   .. autodoc2-docstring:: sxdm.widgets.spec.RoiPlotter.__init__

   .. py:method:: show()
      :canonical: sxdm.widgets.spec.RoiPlotter.show

      .. autodoc2-docstring:: sxdm.widgets.spec.RoiPlotter.show

   .. py:method:: _update_specs()
      :canonical: sxdm.widgets.spec.RoiPlotter._update_specs

      .. autodoc2-docstring:: sxdm.widgets.spec.RoiPlotter._update_specs

   .. py:method:: _update_piezo_coordinates()
      :canonical: sxdm.widgets.spec.RoiPlotter._update_piezo_coordinates

      .. autodoc2-docstring:: sxdm.widgets.spec.RoiPlotter._update_piezo_coordinates

   .. py:method:: _update_pscan(change)
      :canonical: sxdm.widgets.spec.RoiPlotter._update_pscan

      .. autodoc2-docstring:: sxdm.widgets.spec.RoiPlotter._update_pscan

   .. py:method:: _update_roi(change)
      :canonical: sxdm.widgets.spec.RoiPlotter._update_roi

      .. autodoc2-docstring:: sxdm.widgets.spec.RoiPlotter._update_roi

   .. py:method:: _update_norm(change)
      :canonical: sxdm.widgets.spec.RoiPlotter._update_norm

      .. autodoc2-docstring:: sxdm.widgets.spec.RoiPlotter._update_norm

   .. py:method:: _add_crosshar(change)
      :canonical: sxdm.widgets.spec.RoiPlotter._add_crosshar

      .. autodoc2-docstring:: sxdm.widgets.spec.RoiPlotter._add_crosshar

.. py:class:: FramesExplorer(pscan, detector='maxipix', coms=None, img_dir=None)
   :canonical: sxdm.widgets.spec.FramesExplorer

   Bases: :py:obj:`object`

   .. autodoc2-docstring:: sxdm.widgets.spec.FramesExplorer

   .. rubric:: Initialization

   .. autodoc2-docstring:: sxdm.widgets.spec.FramesExplorer.__init__

   .. py:method:: show()
      :canonical: sxdm.widgets.spec.FramesExplorer.show

      .. autodoc2-docstring:: sxdm.widgets.spec.FramesExplorer.show

   .. py:method:: _line_select_callback(eclick, erelease)
      :canonical: sxdm.widgets.spec.FramesExplorer._line_select_callback

      .. autodoc2-docstring:: sxdm.widgets.spec.FramesExplorer._line_select_callback

   .. py:method:: _define_roi(change)
      :canonical: sxdm.widgets.spec.FramesExplorer._define_roi

      .. autodoc2-docstring:: sxdm.widgets.spec.FramesExplorer._define_roi

   .. py:method:: _update_plots()
      :canonical: sxdm.widgets.spec.FramesExplorer._update_plots

      .. autodoc2-docstring:: sxdm.widgets.spec.FramesExplorer._update_plots

   .. py:method:: _on_click(event)
      :canonical: sxdm.widgets.spec.FramesExplorer._on_click

      .. autodoc2-docstring:: sxdm.widgets.spec.FramesExplorer._on_click

   .. py:method:: _on_key(event)
      :canonical: sxdm.widgets.spec.FramesExplorer._on_key

      .. autodoc2-docstring:: sxdm.widgets.spec.FramesExplorer._on_key

   .. py:method:: _update_norm(change)
      :canonical: sxdm.widgets.spec.FramesExplorer._update_norm

      .. autodoc2-docstring:: sxdm.widgets.spec.FramesExplorer._update_norm

   .. py:method:: _add_rois(change)
      :canonical: sxdm.widgets.spec.FramesExplorer._add_rois

      .. autodoc2-docstring:: sxdm.widgets.spec.FramesExplorer._add_rois

   .. py:method:: _update_roi(change)
      :canonical: sxdm.widgets.spec.FramesExplorer._update_roi

      .. autodoc2-docstring:: sxdm.widgets.spec.FramesExplorer._update_roi
