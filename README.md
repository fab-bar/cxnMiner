# Creating the development environment

You can use [conda](https://docs.conda.io/projects/conda/en/latest/index.html)
to install the python version that has been used to run the experiments:

    conda env create -f environment.yml -p .venv

Python packages are managed by pip (with the help of [pip-tools](https://github.com/jazzband/pip-tools)).
requirements.txt contains all the dependencies that are used for the experiments and during development.
It has been created from the dependencies of the package _cxnminer_ given in setup.py and the
additional dependencies given in dev-requirements.in using

    pip-compile setup.py dev-requirements.in --output-file requirements.txt

The dependencise and the package _cxnminer_ can be installed in your environment with the following commands:

    pip install -r requirements.txt 
    pip install -e .

Alternatively pip-sync (from pip-tools) can be used to assure that exactly (and only) the packages
mentioned in requirements.txt are installed:

    pip-sync && pip install -e .
