# Installation

## On Jupyter-SLURM

To use `id01-sxdm` on the ESRF Jupyter Hub server [Jupyter-SLURM](https://jupyter-slurm.esrf.fr/hub/spawn):

* [Spawn a Jupyter-SLURM instance](https://confluence.esrf.fr/display/DAUWK/Jupyter+at+ESRF#JupyteratESRF-StartingJupyterServerStartingaJupyter(Lab)Server).
* Once the instance is spawned the interface shows the contents of the user's home directory on the ESRF cluster. On the right of the interface click on `New` and then `Terminal`. This opens a terminal in the same directory.
* In the terminal, run:
    ```bash
    pip install --quiet ipykernel
    source /data/id01/inhouse/data_analysis/software/pyenvs/sxdm.slurm/bin/activate
    python3 -m ipykernel install --user --name sxdm.slurm
    ```
* Create or open the `.ipynb` of choice and select the `sxdm.slurm` kernel.

## On a local machine

First install `xsocs`:

```bash
pip install git+https://gitlab.esrf.fr/zatterin/xsocs.git#egg=xsocs
```

Then `id01lib`:

```bash
pip install git+https://gitlab.esrf.fr/id01-science/id01-core.git#egg=id01-core
```

Finally this package, `sxdm`:

```bash
pip install git+https://gitlab.esrf.fr/id01-science/id01-sxdm-utils.git#egg=id01-sxdm-utils
```

These steps are necessary as none of these three packages is currently available from the Python Packaging Index (PyPI), as they are not mature enough to be published.

## Installation of Notebook extensions

```bash
pip install --quiet ipympl
/data/id01/inhouse/data_analysis/software/pyenvs/sxdm.slurm/bin/jupyter nbextension install --py --symlink --user --overwrite ipympl
/data/id01/inhouse/data_analysis/software/pyenvs/sxdm.slurm/bin/jupyter nbextension enable ipympl --user --py

pip install ipyvolume -q # will install in sys-prefix, i.e. the virtual env directory
pip install ipyvolume --user -q # needed to enable the extension even if not going to use it

source /data/id01/inhouse/data_analysis/software/pyenvs/sxdm.slurm/bin/activate
/data/id01/inhouse/data_analysis/software/pyenvs/sxdm.slurm/bin/jupyter \
nbextension enable --py ipyvolume # will enable it in sys-prefix
/data/id01/inhouse/data_analysis/software/pyenvs/sxdm.slurm/bin/jupyter \
nbextension enable --py --user ipyvolume # will enable it in ~/.jupyter/nbconfig/tree.json