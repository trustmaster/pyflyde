# Makefile for Python project

# Variables
PYTHON = /usr/bin/env python3
LIB_DIR = examples/mylib
SRC_DIR = flyde
TEST_DIR = tests

# Targets
.PHONY: ts test cover

ts:
	@echo "Building the project..."
	# For each *.py file in the examples/mylib directory run the ./flyde.py gen command to generate TS bindings
	@for file in $(LIB_DIR)/*.py; do \
		./flyde.py gen $$file; \
	done

lint:
	@echo "Running linters..."
	@black $(LIB_DIR) $(TEST_DIR);
	@flake8 $(LIB_DIR) $(TEST_DIR);

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
	@stubgen $(SRC_DIR) -o .;
	@$(PYTHON) -m build;

upload:
	@echo "Uploading the project to PyPI..."
	@twine upload dist/*;
