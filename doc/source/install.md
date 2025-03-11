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

Ensure you have [`git`](https://git-scm.com/) installed on your machine. Open a terminal and run:

```bash
pip install git+https://gitlab.esrf.fr/id01-science/id01-sxdm-utils.git
```

### Installation of Notebook extensions

If using an old version of Jupyter-notebook, the following may be necessary to run the interactive widgets successfuly.

```bash
pip install ipympl
nbextension install --py ipympl
nbextension enable --py ipympl

pip install ipyvolume
nbextension install --py ipyvolume
nbextension enable --py ipyvolume
```
