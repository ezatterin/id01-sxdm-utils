:py:mod:`sxdm.widgets.xsocs`
============================

.. py:module:: sxdm.widgets.xsocs

.. autodoc2-docstring:: sxdm.widgets.xsocs
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`Inspect5DQspace <sxdm.widgets.xsocs.Inspect5DQspace>`
     - .. autodoc2-docstring:: sxdm.widgets.xsocs.Inspect5DQspace
          :summary:

API
~~~

.. py:class:: Inspect5DQspace(maps_dict, path_qspace, projections='2d', init_idx=[10, 10], qspace_roi=np.s_[:, :, :], relim_int=True, coms=None, gauss_fits=None, xsocs_gauss=False)
   :canonical: sxdm.widgets.xsocs.Inspect5DQspace

   Bases: :py:obj:`object`

   .. autodoc2-docstring:: sxdm.widgets.xsocs.Inspect5DQspace

   .. rubric:: Initialization

   .. autodoc2-docstring:: sxdm.widgets.xsocs.Inspect5DQspace.__init__

   .. py:attribute:: rec_ax_idx
      :canonical: sxdm.widgets.xsocs.Inspect5DQspace.rec_ax_idx
      :value: None

      .. autodoc2-docstring:: sxdm.widgets.xsocs.Inspect5DQspace.rec_ax_idx

   .. py:method:: _init_widgets()
      :canonical: sxdm.widgets.xsocs.Inspect5DQspace._init_widgets

      .. autodoc2-docstring:: sxdm.widgets.xsocs.Inspect5DQspace._init_widgets

   .. py:method:: _update_norm(change)
      :canonical: sxdm.widgets.xsocs.Inspect5DQspace._update_norm

      .. autodoc2-docstring:: sxdm.widgets.xsocs.Inspect5DQspace._update_norm

   .. py:method:: _get_rsm()
      :canonical: sxdm.widgets.xsocs.Inspect5DQspace._get_rsm

      .. autodoc2-docstring:: sxdm.widgets.xsocs.Inspect5DQspace._get_rsm

   .. py:method:: _init_fig()
      :canonical: sxdm.widgets.xsocs.Inspect5DQspace._init_fig

      .. autodoc2-docstring:: sxdm.widgets.xsocs.Inspect5DQspace._init_fig

   .. py:method:: _change_plot(change)
      :canonical: sxdm.widgets.xsocs.Inspect5DQspace._change_plot

      .. autodoc2-docstring:: sxdm.widgets.xsocs.Inspect5DQspace._change_plot

   .. py:method:: _onclick(event)
      :canonical: sxdm.widgets.xsocs.Inspect5DQspace._onclick

      .. autodoc2-docstring:: sxdm.widgets.xsocs.Inspect5DQspace._onclick

   .. py:method:: _onkey(event)
      :canonical: sxdm.widgets.xsocs.Inspect5DQspace._onkey

      .. autodoc2-docstring:: sxdm.widgets.xsocs.Inspect5DQspace._onkey

   .. py:method:: _update()
      :canonical: sxdm.widgets.xsocs.Inspect5DQspace._update

      .. autodoc2-docstring:: sxdm.widgets.xsocs.Inspect5DQspace._update

   .. py:method:: show()
      :canonical: sxdm.widgets.xsocs.Inspect5DQspace.show

      .. autodoc2-docstring:: sxdm.widgets.xsocs.Inspect5DQspace.show
