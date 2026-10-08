.PHONY: help install dev test lint build publish clean

help:
	@echo "install       editable install (runtime only)"
	@echo "dev           editable install with dev extras"
	@echo "test          run pytest"
	@echo "lint          ruff check"
	@echo "build         build sdist + wheel into dist/"
	@echo "publish       (disabled) releases are published only by .github/workflows/release.yml"
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

publish:
	@echo "Releases are published only by .github/workflows/release.yml (tag vX.Y.Z)." && exit 1

clean:
	rm -rf build dist ./*.egg-info src/*.egg-info
