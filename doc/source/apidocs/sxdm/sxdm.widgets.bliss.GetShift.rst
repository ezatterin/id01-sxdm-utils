:py:mod:`sxdm.widgets.bliss.GetShift`
=====================================

.. py:module:: sxdm.widgets.bliss.GetShift

.. autodoc2-docstring:: sxdm.widgets.bliss.GetShift
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`GetShift <sxdm.widgets.bliss.GetShift.GetShift>`
     - .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift
          :summary:
   * - :py:obj:`GetShiftCustom <sxdm.widgets.bliss.GetShift.GetShiftCustom>`
     - .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShiftCustom
          :summary:

Data
~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`ipython <sxdm.widgets.bliss.GetShift.ipython>`
     - .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.ipython
          :summary:

API
~~~

.. py:data:: ipython
   :canonical: sxdm.widgets.bliss.GetShift.ipython
   :value: 'get_ipython(...)'

   .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.ipython

.. py:class:: GetShift(path_h5, scan_nos=None, counter_name=None, fixed_clims=None)
   :canonical: sxdm.widgets.bliss.GetShift.GetShift

   Bases: :py:obj:`object`

   .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift

   .. rubric:: Initialization

   .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift.__init__

   .. py:method:: _load_counters_list()
      :canonical: sxdm.widgets.bliss.GetShift.GetShift._load_counters_list

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift._load_counters_list

   .. py:method:: _load_piezo_motor_names()
      :canonical: sxdm.widgets.bliss.GetShift.GetShift._load_piezo_motor_names

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift._load_piezo_motor_names

   .. py:method:: _init_fig()
      :canonical: sxdm.widgets.bliss.GetShift.GetShift._init_fig

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift._init_fig

   .. py:method:: _init_widgets()
      :canonical: sxdm.widgets.bliss.GetShift.GetShift._init_widgets

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift._init_widgets

   .. py:method:: _save_shifts(change)
      :canonical: sxdm.widgets.bliss.GetShift.GetShift._save_shifts

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift._save_shifts

   .. py:method:: _scan_idx_fwd(widget)
      :canonical: sxdm.widgets.bliss.GetShift.GetShift._scan_idx_fwd

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift._scan_idx_fwd

   .. py:method:: _scan_idx_bkw(widget)
      :canonical: sxdm.widgets.bliss.GetShift.GetShift._scan_idx_bkw

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift._scan_idx_bkw

   .. py:method:: _update_norm(change)
      :canonical: sxdm.widgets.bliss.GetShift.GetShift._update_norm

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift._update_norm

   .. py:method:: _update_ref(x, y)
      :canonical: sxdm.widgets.bliss.GetShift.GetShift._update_ref

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift._update_ref

   .. py:method:: _on_click(event)
      :canonical: sxdm.widgets.bliss.GetShift.GetShift._on_click

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift._on_click

   .. py:method:: _onkey(event)
      :canonical: sxdm.widgets.bliss.GetShift.GetShift._onkey

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift._onkey

   .. py:method:: _update_counter(change)
      :canonical: sxdm.widgets.bliss.GetShift.GetShift._update_counter

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift._update_counter

   .. py:method:: _update_mark()
      :canonical: sxdm.widgets.bliss.GetShift.GetShift._update_mark

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift._update_mark

   .. py:method:: _update_scan(change)
      :canonical: sxdm.widgets.bliss.GetShift.GetShift._update_scan

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift._update_scan

   .. py:method:: _apply_shift_counter(change)
      :canonical: sxdm.widgets.bliss.GetShift.GetShift._apply_shift_counter

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift._apply_shift_counter

   .. py:method:: _calc_shifts()
      :canonical: sxdm.widgets.bliss.GetShift.GetShift._calc_shifts

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift._calc_shifts

   .. py:method:: _update_shifts_tab()
      :canonical: sxdm.widgets.bliss.GetShift.GetShift._update_shifts_tab

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift._update_shifts_tab

   .. py:method:: show()
      :canonical: sxdm.widgets.bliss.GetShift.GetShift.show

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShift.show

.. py:class:: GetShiftCustom(img_list, fixed_clims=None, init_shifts=None)
   :canonical: sxdm.widgets.bliss.GetShift.GetShiftCustom

   Bases: :py:obj:`object`

   .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShiftCustom

   .. rubric:: Initialization

   .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShiftCustom.__init__

   .. py:method:: _init_fig()
      :canonical: sxdm.widgets.bliss.GetShift.GetShiftCustom._init_fig

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShiftCustom._init_fig

   .. py:method:: _init_widgets()
      :canonical: sxdm.widgets.bliss.GetShift.GetShiftCustom._init_widgets

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShiftCustom._init_widgets

   .. py:method:: _img_idx_fwd(widget)
      :canonical: sxdm.widgets.bliss.GetShift.GetShiftCustom._img_idx_fwd

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShiftCustom._img_idx_fwd

   .. py:method:: _img_idx_bkw(widget)
      :canonical: sxdm.widgets.bliss.GetShift.GetShiftCustom._img_idx_bkw

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShiftCustom._img_idx_bkw

   .. py:method:: _update_norm(change)
      :canonical: sxdm.widgets.bliss.GetShift.GetShiftCustom._update_norm

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShiftCustom._update_norm

   .. py:method:: show()
      :canonical: sxdm.widgets.bliss.GetShift.GetShiftCustom.show

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShiftCustom.show

   .. py:method:: _on_click(event)
      :canonical: sxdm.widgets.bliss.GetShift.GetShiftCustom._on_click

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShiftCustom._on_click

   .. py:method:: _update_mark()
      :canonical: sxdm.widgets.bliss.GetShift.GetShiftCustom._update_mark

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShiftCustom._update_mark

   .. py:method:: _update_scan(change)
      :canonical: sxdm.widgets.bliss.GetShift.GetShiftCustom._update_scan

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShiftCustom._update_scan

   .. py:method:: _apply_shift_counter(change)
      :canonical: sxdm.widgets.bliss.GetShift.GetShiftCustom._apply_shift_counter

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShiftCustom._apply_shift_counter

   .. py:method:: _calc_shifts()
      :canonical: sxdm.widgets.bliss.GetShift.GetShiftCustom._calc_shifts

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShiftCustom._calc_shifts

   .. py:method:: _update_shifts_tab()
      :canonical: sxdm.widgets.bliss.GetShift.GetShiftCustom._update_shifts_tab

      .. autodoc2-docstring:: sxdm.widgets.bliss.GetShift.GetShiftCustom._update_shifts_tab
