# Contribute

Thanks for considering contributing to `id01-sxdm`!

## How?

In different ways:

* [Report a bug](https://gitlab.esrf.fr/id01-science/id01-sxdm-utils/-/issues/new)
* Add a new feature
* Fix a bug
* Improve the documentation

## Setup

Follow these steps for a developer installation:

### On SLURM @ ESRF

Source the `poetry` virtual environment,

```bash
source /data/id01/inhouse/data_analysis/software/pyenvs/poetry.jupyter-slurm/bin/activate
```

clone the repo:

```bash
git clone https://gitlab.esrf.fr/id01-science/id01-sxdm-utils.git
```

in the `id01-sxdm-utils` folder run:

```bash
poetry config virtualenvs.in-project true # isolate sxdm venv from poetry venv - installs in .venv within project directory
poetry install
poetry run pre-commit install
poetry run pre-commit run --all-files
```

If planning on using Jupyter, add a kernel:

```bash
poetry run python -m ipykernel install --user --name sxdm.poetry
```

### On a local machine

1. Install the packaging and dependency manager [poetry](https://python-poetry.org/docs/#installation);
2. Clone the [id01-sxdm](https://gitlab.esrf.fr/id01-science/id01-sxdm-utils) repository;
3. Run `poetry install` into the cloned repo, to install all dependencies;
4. Run `poetry run pre-commit install` into the repo, to install the pre-commit hooks.

## Guidelines

**Under construction!**

<!-- * Make sure **not to commit** the `poetry.lock` file. -->
