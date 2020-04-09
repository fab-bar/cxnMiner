REQUIREMENTS_TXT=  # requirements are handled with pip-tools pip-sync

include Makefile.venv
Makefile.venv:
	curl \
		-o Makefile.fetched \
		-L "https://github.com/sio/Makefile.venv/raw/v2019.12.05/Makefile.venv"
	echo "1b0a2f89b322ea86958d63ed4ae718846ccaaf939e5e24180524f28dede238ba *Makefile.fetched" \
		| sha256sum --check - \
		&& mv Makefile.fetched Makefile.venv

.PHONY: myvenv
myvenv: $(VENV)/$(MARKER).pipsync

.PHONY: piptools
piptools: $(VENV)/$(MARKER).piptools

$(VENV)/$(MARKER).piptools: | venv
	$(VENV)/pip install --upgrade pip-tools
	touch $(VENV)/$(MARKER).piptools

$(VENV)/$(MARKER).pipsync: requirements-dev.txt | venv piptools
	$(VENV)/pip-sync requirements-dev.txt
	$(VENV)/pip install -e .
	touch $(VENV)/$(MARKER).pipsync

requirements-dev.txt: setup.py requirements-dev.in requirements-test.in
	$(VENV)/pip-compile $(UPGRADE) setup.py requirements-dev.in requirements-test.in --output-file requirements-dev.txt

requirements-test.txt: setup.py requirements-test.in | myvenv
	$(VENV)/pip-compile $(UPGRADE) setup.py requirements-test.in --output-file requirements-test.txt

requirements-docs.txt: setup.py requirements-docs.in | myvenv
	$(VENV)/pip-compile $(UPGRADE) requirements-docs.in --output-file requirements-docs.txt

#####

.PHONY: upgrade
upgrade:
	 make UPGRADE=--upgrade \
	-W requirements-dev.in -W requirements-test.in -W requirements-docs.in \
	requirements-dev.txt requirements-test.txt requirements-docs.txt

.PHONY: docs
docs: requirements-docs.txt badges myvenv
	$(VENV)/tox -e docs

.PHONY: test
test: requirements-test.txt myvenv
	$(VENV)/tox

.PHONY: coverage
coverage: requirements-test.txt myvenv
	$(VENV)/pytest --cov=cxnminer
	$(VENV)/coverage html -d .coverage_html

.PHONY: badges
badges: coverage myvenv
	$(VENV)/python -m pybadges --left-text=license --right-text=MIT > _static/license.svg
	$(VENV)/coverage-badge -fo _static/coverage.svg
