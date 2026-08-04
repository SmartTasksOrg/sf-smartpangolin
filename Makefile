.PHONY: help install dev test lint build publish-test publish clean

help:
	@echo "install       editable install (runtime only)"
	@echo "dev           editable install with dev extras"
	@echo "test          run pytest"
	@echo "lint          ruff check"
	@echo "build         build sdist + wheel into dist/"
	@echo "publish-test  upload to TestPyPI"
	@echo "publish       upload to PyPI"
	@echo "clean         remove build artifacts"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	python -m pytest

lint:
	ruff check src tests

build: clean
	python -m build

publish-test: build
	python -m twine upload --repository testpypi dist/*

publish: build
	python -m twine check dist/*
	python -m twine upload dist/*

clean:
	rm -rf build dist ./*.egg-info src/*.egg-info
