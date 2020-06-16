.. Jamie documentation master file

.. _GitHub: https://github.com/softwaresaved/jobs-analysis

Jobs Analysis using Machine Information Extraction
==================================================

Jobs Analysis using Machine Information Extraction (JAMIE) is a tool that aims
to monitor and analyse the number of academic jobs, mainly in the UK, that
require software skills.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Jamie is hosted on GitHub_. This page provides the *API*, or *developer
documentation* for ``jamie``.

Quickstart
==========

Jamie is available on GNU/Linux, MacOS and Windows. To install using **pip**:

.. code:: bash

   git clone -b jamie git@github.com:softwaresaved/jobs-analysis.git
   cd jobs-analysis
   python3 -m venv venv
   source venv/bin/activate
   pip install .

See the workflow for more information about how to use Jamie, or look at the API documentation if you want to use Jamie from a Python environment (such as a Jupyter notebook):

.. toctree::
   :maxdepth: 2

   workflow

API documentation
=================

.. toctree::
   :maxdepth: 2

   features
   scrape
   snapshots
   models
   config
   predict
   cli
