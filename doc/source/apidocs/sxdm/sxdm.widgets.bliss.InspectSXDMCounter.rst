:py:mod:`sxdm.widgets.bliss.InspectSXDMCounter`
===============================================

.. py:module:: sxdm.widgets.bliss.InspectSXDMCounter

.. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`InspectSXDMCounter <sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter>`
     - .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter
          :summary:

Functions
~~~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`InspectROI <sxdm.widgets.bliss.InspectSXDMCounter.InspectROI>`
     - .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectROI
          :summary:

Data
~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`ipython <sxdm.widgets.bliss.InspectSXDMCounter.ipython>`
     - .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.ipython
          :summary:

API
~~~

.. py:data:: ipython
   :canonical: sxdm.widgets.bliss.InspectSXDMCounter.ipython
   :value: 'get_ipython(...)'

   .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.ipython

.. py:class:: InspectSXDMCounter(path_dset, default_counter=None, counter_list=None, init_scan_no=None, fixed_clims=None, show_scan_nos=None)
   :canonical: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter

   Bases: :py:obj:`object`

   .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter

   .. rubric:: Initialization

   .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter.__init__

   .. py:method:: _init_fig()
      :canonical: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._init_fig

      .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._init_fig

   .. py:method:: _init_widgets()
      :canonical: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._init_widgets

      .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._init_widgets

   .. py:method:: _load_counters()
      :canonical: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._load_counters

      .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._load_counters

   .. py:method:: _on_click(event)
      :canonical: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._on_click

      .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._on_click

   .. py:method:: _add_crosshair(change)
      :canonical: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._add_crosshair

      .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._add_crosshair

   .. py:method:: _flip_xaxis(change)
      :canonical: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._flip_xaxis

      .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._flip_xaxis

   .. py:method:: _flip_yaxis(change)
      :canonical: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._flip_yaxis

      .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._flip_yaxis

   .. py:method:: _update_roi(change)
      :canonical: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._update_roi

      .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._update_roi

   .. py:method:: _update_norm(change)
      :canonical: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._update_norm

      .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._update_norm

   .. py:method:: _get_piezo_motor_names()
      :canonical: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._get_piezo_motor_names

      .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._get_piezo_motor_names

   .. py:method:: _get_piezo_coordinates()
      :canonical: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._get_piezo_coordinates

      .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._get_piezo_coordinates

   .. py:method:: _update_img_extent()
      :canonical: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._update_img_extent

      .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._update_img_extent

   .. py:method:: _update_specs()
      :canonical: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._update_specs

      .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._update_specs

   .. py:method:: _get_sharpness()
      :canonical: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._get_sharpness

      .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._get_sharpness

   .. py:method:: _update_scan(change)
      :canonical: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._update_scan

      .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter._update_scan

   .. py:method:: show()
      :canonical: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter.show

      .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectSXDMCounter.show

.. py:function:: InspectROI(*args, **kwargs)
   :canonical: sxdm.widgets.bliss.InspectSXDMCounter.InspectROI

   .. autodoc2-docstring:: sxdm.widgets.bliss.InspectSXDMCounter.InspectROI
