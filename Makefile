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


clean:
	find . -name '*.pyc' -delete
	$(VIRTUAL_ENV)/bin/coverage erase


deps: $(PRE_DEPS)
	$(VIRTUAL_ENV)/bin/pip install -e .
	$(VIRTUAL_ENV)/bin/pip install -r dev-requirements.txt


test: $(PRE_TEST)
	$(VIRTUAL_ENV)/bin/pytest


.coverage: $(PRE_TEST)
	$(VIRTUAL_ENV)/bin/coverage run $(VIRTUAL_ENV)/bin/py.test
	$(VIRTUAL_ENV)/bin/coverage html -i pypiprivate/*.py
	@echo "Coverage report: file://$(ROOT_DIR)/htmlcov/index.html"
