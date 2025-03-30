# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath("../.."))


# -- Project information -----------------------------------------------------

project = "id01-sxdm-utils"
copyright = "2024, Edoardo Zatterin"
author = "Edoardo Zatterin"

# The full version, including alpha/beta/rc tags
release = "0.1.0"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "myst_nb",
    "autodoc2",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.mathjax",
    "IPython.sphinxext.ipython_console_highlighting",
    "sphinx_copybutton",
    "sphinx_design",
]

autodoc2_packages = ["../../sxdm"]
autodoc2_hidden_objects = ["private"]
autodoc2_render_plugin = "myst"

myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_image",
]

myst_url_schemes = ("http", "https", "mailto")

nb_execution_mode = "force"
nb_execution_show_tb = True
nb_execution_excludepatterns = ["notebook_templates/*"]
nb_execution_timeout = 600

napoleon_google_docstring = False
napoleon_use_param = False
napoleon_use_ivar = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_tests.md", "build"]


# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_title = "ID01-SXDM Documentation"

html_theme_options = {
    "source_view_link": "https://gitlab.esrf.fr/id01-science/id01-sxdm-utils/raw/main/doc/source/{filename}",
    "source_edit_link": "https://gitlab.esrf.fr/id01-science/id01-sxdm-utils/edit/main/doc/source/{filename}",
    "footer_icons": [
        {
            "name": "GitLab",
            "url": "https://gitlab.esrf.fr/id01-science/id01-sxdm-utils",
            "html": "",
            "class": "fa-brands fa-solid fa-gitlab fa-2x",
        },
    ],
}

html_css_files = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/fontawesome.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/solid.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/brands.min.css",
]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ["_static"]

# get __init__ docstrings under the class
autoclass_content = "both"

# logo
html_logo = "img/logo.png"
