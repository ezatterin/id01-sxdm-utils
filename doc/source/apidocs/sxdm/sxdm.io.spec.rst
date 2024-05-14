:py:mod:`sxdm.io.spec`
======================

.. py:module:: sxdm.io.spec

.. autodoc2-docstring:: sxdm.io.spec
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`FastSpecFile <sxdm.io.spec.FastSpecFile>`
     - .. autodoc2-docstring:: sxdm.io.spec.FastSpecFile
          :summary:
   * - :py:obj:`PiezoScan <sxdm.io.spec.PiezoScan>`
     - .. autodoc2-docstring:: sxdm.io.spec.PiezoScan
          :summary:

API
~~~

.. py:class:: FastSpecFile(filename)
   :canonical: sxdm.io.spec.FastSpecFile

   Bases: :py:obj:`silx.io.specfile.SpecFile`

   .. autodoc2-docstring:: sxdm.io.spec.FastSpecFile

   .. rubric:: Initialization

   .. autodoc2-docstring:: sxdm.io.spec.FastSpecFile.__init__

   .. py:method:: __new__(filename)
      :canonical: sxdm.io.spec.FastSpecFile.__new__

      .. autodoc2-docstring:: sxdm.io.spec.FastSpecFile.__new__

   .. py:method:: __str__()
      :canonical: sxdm.io.spec.FastSpecFile.__str__

      .. autodoc2-docstring:: sxdm.io.spec.FastSpecFile.__str__

   .. py:method:: _repr_html_()
      :canonical: sxdm.io.spec.FastSpecFile._repr_html_

      .. autodoc2-docstring:: sxdm.io.spec.FastSpecFile._repr_html_

   .. py:method:: __getitem__(key)
      :canonical: sxdm.io.spec.FastSpecFile.__getitem__

      .. autodoc2-docstring:: sxdm.io.spec.FastSpecFile.__getitem__

.. py:class:: PiezoScan(fast_specfile, scan_number)
   :canonical: sxdm.io.spec.PiezoScan

   Bases: :py:obj:`silx.io.specfile.Scan`

   .. autodoc2-docstring:: sxdm.io.spec.PiezoScan

   .. rubric:: Initialization

   .. autodoc2-docstring:: sxdm.io.spec.PiezoScan.__init__

   .. py:attribute:: motordef
      :canonical: sxdm.io.spec.PiezoScan.motordef
      :value: 'dict(...)'

      .. autodoc2-docstring:: sxdm.io.spec.PiezoScan.motordef

   .. py:method:: __str__()
      :canonical: sxdm.io.spec.PiezoScan.__str__

      .. autodoc2-docstring:: sxdm.io.spec.PiezoScan.__str__

   .. py:method:: _repr_html_()
      :canonical: sxdm.io.spec.PiezoScan._repr_html_

      .. autodoc2-docstring:: sxdm.io.spec.PiezoScan._repr_html_

   .. py:method:: get_roidata(counter)
      :canonical: sxdm.io.spec.PiezoScan.get_roidata

      .. autodoc2-docstring:: sxdm.io.spec.PiezoScan.get_roidata

   .. py:method:: get_piezo_coordinates()
      :canonical: sxdm.io.spec.PiezoScan.get_piezo_coordinates

      .. autodoc2-docstring:: sxdm.io.spec.PiezoScan.get_piezo_coordinates

   .. py:method:: get_positioner(motor_name)
      :canonical: sxdm.io.spec.PiezoScan.get_positioner

      .. autodoc2-docstring:: sxdm.io.spec.PiezoScan.get_positioner

   .. py:method:: get_motorpos(motor_name)
      :canonical: sxdm.io.spec.PiezoScan.get_motorpos

      .. autodoc2-docstring:: sxdm.io.spec.PiezoScan.get_motorpos

   .. py:method:: get_roipos()
      :canonical: sxdm.io.spec.PiezoScan.get_roipos

      .. autodoc2-docstring:: sxdm.io.spec.PiezoScan.get_roipos

   .. py:method:: get_edf_filename()
      :canonical: sxdm.io.spec.PiezoScan.get_edf_filename

      .. autodoc2-docstring:: sxdm.io.spec.PiezoScan.get_edf_filename

   .. py:method:: get_detector_frames(img_dir=None, entry_name='scan_0')
      :canonical: sxdm.io.spec.PiezoScan.get_detector_frames

      .. autodoc2-docstring:: sxdm.io.spec.PiezoScan.get_detector_frames

   .. py:method:: get_detcalib()
      :canonical: sxdm.io.spec.PiezoScan.get_detcalib

      .. autodoc2-docstring:: sxdm.io.spec.PiezoScan.get_detcalib

   .. py:method:: calc_qspace_coordinates(cen_pix=None, detector_distance=None, energy=None, detector='maxipix', ipdir=(1, 0, 0), ndir=(0, 0, 1), ignore_mpx_motors=True)
      :canonical: sxdm.io.spec.PiezoScan.calc_qspace_coordinates

      .. autodoc2-docstring:: sxdm.io.spec.PiezoScan.calc_qspace_coordinates

   .. py:method:: calc_coms(roi=None, qspace=False, calc_std=False)
      :canonical: sxdm.io.spec.PiezoScan.calc_coms

      .. autodoc2-docstring:: sxdm.io.spec.PiezoScan.calc_coms

   .. py:method:: fit_gaussian(index, roi=None, **qspace_kwargs)
      :canonical: sxdm.io.spec.PiezoScan.fit_gaussian

      .. autodoc2-docstring:: sxdm.io.spec.PiezoScan.fit_gaussian
