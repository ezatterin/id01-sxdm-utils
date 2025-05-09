# https://www.sphinx-doc.org/en/master/usage/configuration.html

## imports and path setop

import os
import sys
from datetime import date

sys.path.insert(0, os.path.abspath("../.."))

## project info

project = "id01-sxdm-utils"
copyright = "2024, Edoardo Zatterin"
author = "Edoardo Zatterin"
year = date.today().year

release = "0.1.0"


# -- General configuration ---------------------------------------------------

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
    "attrs_block",
]

myst_heading_anchors = 3

myst_url_schemes = ("http", "https", "mailto")

nb_execution_mode = "cache"
nb_execution_show_tb = True
nb_execution_excludepatterns = ["notebook_templates/*"]
nb_execution_timeout = 600

# Remap any notebook kernel name matching the regex to "python3"
nb_kernel_rgx_aliases = {r".*": "python3"}

napoleon_google_docstring = False
napoleon_use_param = False
napoleon_use_ivar = True

templates_path = ["_templates"]

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
            "class": "fa-brands fa-solid fa-gitlab fa-lg",
        },
        {
            "name": "GitHub",
            "url": "https://github.com/ezatterin/id01-sxdm-utils",
            "html": "",
            "class": "fa-brands fa-solid fa-github fa-lg",
        },
    ],
}

html_css_files = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/fontawesome.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/solid.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/brands.min.css",
]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ["_static"]

# get __init__ docstrings under the class
autoclass_content = "both"

# logo
html_logo = "img/logo.png"
