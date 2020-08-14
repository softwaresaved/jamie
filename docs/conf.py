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
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = "Jamie"
copyright = "2020, Software Sustainability Institute"
author = "Software Sustainability Institute"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon", "sphinx.ext.intersphinx"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://docs.scipy.org/doc/numpy/", None),
}
napoleon_use_rtype = False
# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "alabaster"
html_static_path = ["_static"]
html_css_path = ["custom.css"]
html_theme_options = {
    "code_font_size": "10pt",
    "body_text": "#24292e",
    "anchor": "#24292e",
    "pre_bg": "#f6f8fa",
    "code_font_family": "Consolas,Menlo,'Liberation Mono','DejaVu Sans Mono','Bitstream Vera Sans Mono',monospace",
    "link": "#0366d6",
    "logo": "logo.png",
    "github_user": "softwaresaved",
    "github_repo": "jamie",
    "github_button": True,
    "description": (
        "Jobs Analysis using Machine Information Extraction (JAMIE)"
        " monitors the number of academic jobs in the UK that require software skills"
    ),
    "font_family": (
        "-apple-system,system-ui,BlinkMacSystemFont,'Segoe UI',"
        "Roboto,Cantarell,Ubuntu,'Helvetica Neue',Arial,sans-serif"
    ),
    "font_size": "12pt",
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
