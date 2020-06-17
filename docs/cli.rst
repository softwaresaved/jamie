Command Line Interface
----------------------

API Description of the CLI interface to Jamie. This module allows operation of the Jamie CLI from a Python environment such as a Jupyter notebook. For information about parameters, see :doc:`workflow`. You can pass a custom configuration path to :class:`jamie.Jamie` as well.

Example
=======

Running a standard pipeline in a Python environment:

>>> from jamie import Jamie
>>> jobs = Jamie()
>>> print(jobs.cf)  # show current configuration
>>> jobs.scrape()
>>> jobs.load()
>>> jobs.train("2020-01-01T12-00-00")  # train using specified snapshot
>>> jobs.predict()
>>> jobs.report()

API
===

.. autoclass:: jamie.Jamie
    :members:
