# Makefile for pypiprivate

.PHONY: deps test

ROOT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

# If the env. var VIRTUAL_ENV is not set, a new virtualenv will be
# created in the ./.env directory and will be setup with all deps for
# running the tests.
ifndef VIRTUAL_ENV
	VIRTUAL_ENV ?= .env
	PRE_TEST := deps
	PRE_DEPS := .env
else
	PRE_TEST :=
	PRE_DEPS :=
endif


.env:
	virtualenv -p python3 .env
	$(VIRTUAL_ENV)/bin/pip install -U pip setuptools

bandit:
	$(VIRTUAL_ENV)/bin/pip install bandit
	$(VIRTUAL_ENV)/bin/bandit --verbose --ignore-nosec --recursive -r pythia  --exclude venv  -o bandit_report.json -f json ||true

check:
	$(VIRTUAL_ENV)/bin/pip install dependency-check
	$(VIRTUAL_ENV)/bin/dependency-check --disableAssembly -s .  --project "$(shell $(VIRTUAL_ENV)/bin/python setup.py --name)" --exclude ".git/**" --exclude ".venv/**" --exclude "**/__pycache__/**" --exclude ".tox/**" --format "ALL"

clean:
	find . -name '*.pyc' -delete
	$(VIRTUAL_ENV)/bin/coverage erase
	rm -rf .reports
	rm -rf .coverage coverage.xml pylint.txt dependency-check-report.*

coverage: clean deps
	$(VIRTUAL_ENV)/bin/pip install coverage
	$(VIRTUAL_ENV)/bin/coverage run -m pytest
	$(VIRTUAL_ENV)/bin/coverage xml

deps: $(PRE_DEPS)
	$(VIRTUAL_ENV)/bin/pip install -e .
	$(VIRTUAL_ENV)/bin/pip install -r dev-requirements.txt

pylint:
	$(VIRTUAL_ENV)/bin/pip install pylint
	$(VIRTUAL_ENV)/bin/pylint --exit-zero cockpit/ tests/  -r n --msg-template="{path}:{line}:[{msg_id}({symbol}), {obj}] {msg}" | tee pylint.txt

safety: clean deps
	$(VIRTUAL_ENV)/bin/pip install safety
	$(VIRTUAL_ENV)/bin/safety check
	$(VIRTUAL_ENV)/bin/safety scan

sonar: coverage check bandit pylint

test: $(PRE_TEST)
	$(VIRTUAL_ENV)/bin/pytest
