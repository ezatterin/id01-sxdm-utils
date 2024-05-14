:py:mod:`sxdm.io.utils`
=======================

.. py:module:: sxdm.io.utils

.. autodoc2-docstring:: sxdm.io.utils
   :allowtitles:

Module Contents
---------------

Functions
~~~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`list_available_counters <sxdm.io.utils.list_available_counters>`
     - .. autodoc2-docstring:: sxdm.io.utils.list_available_counters
          :summary:
   * - :py:obj:`_get_chunk_indexes <sxdm.io.utils._get_chunk_indexes>`
     - .. autodoc2-docstring:: sxdm.io.utils._get_chunk_indexes
          :summary:
   * - :py:obj:`_get_chunk_indexes_detector <sxdm.io.utils._get_chunk_indexes_detector>`
     - .. autodoc2-docstring:: sxdm.io.utils._get_chunk_indexes_detector
          :summary:
   * - :py:obj:`_get_qspace_avg_chunk <sxdm.io.utils._get_qspace_avg_chunk>`
     - .. autodoc2-docstring:: sxdm.io.utils._get_qspace_avg_chunk
          :summary:

API
~~~

.. py:function:: list_available_counters(h5f, scan_no)
   :canonical: sxdm.io.utils.list_available_counters

   .. autodoc2-docstring:: sxdm.io.utils.list_available_counters

.. py:function:: _get_chunk_indexes(path_h5, path_in_h5, n_proc=None)
   :canonical: sxdm.io.utils._get_chunk_indexes

   .. autodoc2-docstring:: sxdm.io.utils._get_chunk_indexes

.. py:function:: _get_chunk_indexes_detector(path_h5, path_in_h5, n_chunks=3, roi=None)
   :canonical: sxdm.io.utils._get_chunk_indexes_detector

   .. autodoc2-docstring:: sxdm.io.utils._get_chunk_indexes_detector

.. py:function:: _get_qspace_avg_chunk(path_h5, path_in_h5, idx_mask, idx_range)
   :canonical: sxdm.io.utils._get_qspace_avg_chunk

   .. autodoc2-docstring:: sxdm.io.utils._get_qspace_avg_chunk
