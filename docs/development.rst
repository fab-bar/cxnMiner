Creating the development environment
====================================

You can use `conda <https://docs.conda.io/projects/conda/en/latest/index.html>`_
to install the python version that has been used to run the experiments:

.. code-block:: bash

   conda env create -f environment.yml -p .venv

Python packages are managed by pip (with the help of `pip-tools
<https://github.com/jazzband/pip-tools>`_). requirements.txt contains all the
dependencies that are used for the experiments and during development. It has
been created from the dependencies of the package *cxnminer* given in
setup.py and the additional dependencies given in dev-requirements.in using

.. code-block:: bash

   pip-compile setup.py dev-requirements.in --output-file requirements.txt

The dependencise and the package *cxnminer* can be installed in your environment with the following commands:

.. code-block:: bash

   pip install -r requirements.txt 
   pip install -e .

Alternatively pip-sync (from pip-tools) can be used to assure that exactly (and only) the packages
mentioned in requirements.txt are installed:

.. code-block:: bash

   pip-sync && pip install -e .

Tests
=====

Tests are run using `pytest <https://docs.pytest.org>`_ with `tox
<https://tox.readthedocs.io/>`_ handling tests for multiple python versions
(3.5, 3.6, 3.7 and 3.8)

Documentation
=============

The documentation is built using `sphinx <https://www.sphinx-doc.org/>`_. The
virtual environment containing sphinx and the other packages that are needed is
handled by `tox <https://tox.readthedocs.io/>`_. The packages are defined in
requirments-docs.txt which is managed with the help of pip-tools as well.

.. code-block:: bash

   pip-compile requirements-docs.in --output-file requirements-docs.txt

To create the documentation run:

.. code-block:: bash
           
   tox -e docs
