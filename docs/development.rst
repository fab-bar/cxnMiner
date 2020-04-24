Creating the development environment
====================================

`pyenv <https://github.com/pyenv/pyenv>`_ is used to manage the different
versions of Python that are used for the experiments and for testing. If you
have pyenv installed and activated, pyenv will make the necessary python
versions available as they are listed in `.python_version`. The version listed
first is the one that has been used during development.

All the dependencies that are used for the experiments and during development
are contained in `requirements-dev.txt` which is managed with the help of
`pip-tools <https://github.com/jazzband/pip-tools>`_).

It has been created from the dependencies of the package *cxnminer* given
in setup.py and the additional dependencies given in requirements-dev.in and
requirements-test.in using

.. code-block:: bash

   pip-compile setup.py requirements-dev.in requirements-test.in --output-file requirements-dev.txt

.. note::

   If pip-compile fails (``No module named 'versioneer'``), the
   package *cxnminer* has to be installed into the environment first.
   In order to do this make sure that a recent version of pip is installed
   (> 20) and run :code:`pip install -e .`.

The dependencies and the package *cxnminer* can be installed in your environment with the following commands:

.. code-block:: bash

   pip install -r requirements-dev.txt
   pip install -e .

Alternatively pip-sync (from pip-tools) can be used to assure that exactly (and only) the packages
mentioned in requirements.txt are installed:

.. code-block:: bash

   pip-sync requirements-dev.txt && pip install -e .

Makefile
--------

The development environment can be managed using `make`. The contained Makefile
uses `Makefile.venv <https://github.com/sio/Makefile.venv/>`_ to create and
update a virtual environment. The file contains the following targets:

upgrade
  Upgrade the dependencies (running the `pip-compile` commands with `--upgrade`).
test
  Run the :ref:`tests <tests>`.
docs
  Build the :ref:`documentation <docs>`.
coverage
  Create coverage reports for the :ref:`tests <tests>`. A `HTML report
  <https://coverage.readthedocs.io/en/coverage-5.0.3/cmd.html#html-annotation>`_
  is created in the folder .coverage_html.

.. _tests:

Tests
=====

Tests are run using `pytest <https://docs.pytest.org>`_ with `tox
<https://tox.readthedocs.io/>`_ handling tests for multiple python versions
(3.6, 3.7 and 3.8). The requirements that are used when running the tests,
are given in requirements-test.txt which is managed with the help of pip-tools
as well.

.. code-block:: bash

   pip-compile setup.py requirements-test.in --output-file requirements-test.txt

Additionaly the environment `dev` uses the python version mainly used during
development with the dependencies installed from requirements-dev.txt instead of
requirements-test.txt.

Coverage reports are created using `pytest-cov
<https://pytest-cov.readthedocs.io>`_.:

.. code-block:: bash

   pytest --cov=cxnminer

.. _docs:

Documentation
=============

The documentation is built using `sphinx <https://www.sphinx-doc.org/>`_. The
virtual environment containing sphinx and the other packages that are needed is
handled by `tox <https://tox.readthedocs.io/>`_. The packages are defined in
requirements-docs.txt which is managed with the help of pip-tools as well.

.. code-block:: bash

   pip-compile requirements-docs.in --output-file requirements-docs.txt

To create the documentation run:

.. code-block:: bash
           
   tox -e docs
