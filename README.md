[![pipeline status](https://gitlab.esrf.fr/id01-science/id01-sxdm-utils/badges/main/pipeline.svg)](https://gitlab.esrf.fr/id01-science/id01-sxdm-utils/-/commits/main) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.10777666.svg)](https://doi.org/10.5281/zenodo.10777666)

[[_TOC_]]

<div class="alert alert-block alert-warning"> 
This readme is a work in progress! Send me an email if needed.
</div>

[Documentation](https://id01-science.gitlab-pages.esrf.fr/id01-sxdm-utils)

# Quick access to tutorials

A Jupyter-SLURM instance is automatically spawned.

* [4D-SXDM](https://jupyter-slurm.esrf.fr/hub/spawn?partition=jupyter-nice&jupyterlab=False&nprocs=10&runtime=00:10:00&root_dir=/&default_url=/tree/data/id01/inhouse/zatterin/shared/id01-sxdm-utils/examples/4D-SXDM_tutorial-BLISS.ipynb&environment_path=/data/id01/inhouse/data_analysis/software/pyenvs/sxdm.slurm/bin)
* [5D-SXDM](https://jupyter-slurm.esrf.fr/hub/spawn?partition=jupyter-nice&jupyterlab=False&nprocs=10&runtime=00:10:00&root_dir=/&default_url=/tree/data/id01/inhouse/zatterin/shared/id01-sxdm-utils/examples/5D-SXDM_tutorial-BLISS.ipynb&environment_path=/data/id01/inhouse/data_analysis/software/pyenvs/sxdm.slurm/bin)


# How to run the tutorial notebooks on Jupyter-slurm

1. Go to the [Jupyter-SLURM hub](https://jupyter-slurm.esrf.fr/). 
2. Log in with the ESRF SSO.
3. Spawn an instance with 1/4 of a node (for 4D-SXDM) or the full node (for 5D-SXDM) and the desired time limit.
4. Once the instance is spawned the interface shows the contents of the user's home directory on the NICE cluster. On the right of the interface click on `New` and then `Terminal`. This opens a terminal in the same directory.
5. Clone the `sxdm` repository by pasting `git clone https://gitlab.esrf.fr/id01-science/id01-sxdm-utils.git` in the terminal. 
    * If a connection error appears, type `export no_proxy='.esrf.fr'` and try again.
6. Close the terminal.
7. Navigate to `id01-sxdm-utils/examples/`
8. Click on the notebook!

# Installation on a local machine

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

# Install kernel

```bash
pip3 install --quiet ipykernel
source /data/id01/inhouse/data_analysis/software/pyenvs/sxdm.slurm/bin/activate
python3 -m ipykernel install --user --name sxdm.slurm
```

# Maybe install JS stuff

```bash
pip3 install --quiet ipympl
/data/id01/inhouse/data_analysis/software/pyenvs/sxdm.slurm/bin/jupyter nbextension install --py --symlink --user --overwrite ipympl
/data/id01/inhouse/data_analysis/software/pyenvs/sxdm.slurm/bin/jupyter nbextension enable ipympl --user --py

pip install ipyvolume -q # will install in sys-prefix, i.e. the virtual env directory
pip install ipyvolume --user -q # needed to enable the extension even if not going to use it

source /data/id01/inhouse/data_analysis/software/pyenvs/sxdm.slurm/bin/activate
/data/id01/inhouse/data_analysis/software/pyenvs/sxdm.slurm/bin/jupyter \
nbextension enable --py ipyvolume # will enable it in sys-prefix
/data/id01/inhouse/data_analysis/software/pyenvs/sxdm.slurm/bin/jupyter \
nbextension enable --py --user ipyvolume # will enable it in ~/.jupyter/nbconfig/tree.json
```
