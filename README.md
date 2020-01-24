# Creating the (development) environment

You can use [conda](https://docs.conda.io/projects/conda/en/latest/index.html)
to install the python version used to run the experiments:

    conda env create -f environment.yml -p .venv

Python packages are managed by pip (with the help of [pip-tools](https://github.com/jazzband/pip-tools)).
requirements.txt contains all the dependencies that are used for the experiments.
dev-requirements.txt contains further packages and tools that have been used during development.
They can be installed with the following commands:

    pip install -r requirements.txt
    pip install -r dev-requirements.txt

Alternatively pip-sync (from pip-tools) can be used to assure that exactly (and only) the packages
mentioned in the requirements-files are installed:

    pip-sync dev-requirements.txt requirements.txt
