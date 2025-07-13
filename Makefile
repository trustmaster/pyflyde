# Makefile for Python project

# Variables
PYTHON = /usr/bin/env python3
LIB_DIR = examples/mylib
SRC_DIR = flyde
TEST_DIR = tests

# Targets
.PHONY: gen test cover

gen:
	@echo "Generating component definitions..."
	# Generate JSON definitions for the examples/mylib directory
	@./pyflyde gen $(LIB_DIR)/

lint:
	@echo "Running linters..."
	@black $(LIB_DIR) $(TEST_DIR);
	@flake8 $(LIB_DIR) $(TEST_DIR);

stubgen:
	@echo "Generating type stubs..."
	@rm -f $(SRC_DIR)/*.pyi;
	@stubgen $(SRC_DIR) --include-docstrings --include-private -o .;

test:
	@echo "Running tests..."
	@$(PYTHON) -m unittest discover -s $(TEST_DIR) -p "test_$(if $(mod),$(mod),*).py";

cover:
	@echo "Running tests with coverage..."
	@coverage run -m unittest discover -s $(TEST_DIR) -p "test_*.py" ;

report:
	@coverage report -m --skip-empty --omit="tests/*";

venv-activate:
	@echo "Activating virtual environment..."
	@source .venv/bin/activate;

builddist:
	@echo "Building the project for distribution..."
	@rm -f ./dist/*
	@$(PYTHON) -m build;

release: lint test stubgen gen builddist
	@echo "Releasing the project...";

upload:
	@echo "Uploading the project to PyPI..."
	@twine upload dist/*;
