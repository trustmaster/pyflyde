# Makefile for Python project

# Variables
PYTHON = /usr/bin/env python3
LIB_DIR = examples/mylib
TEST_DIR = tests

# Targets
.PHONY: ts test

ts:
	@echo "Building the project..."
	# For each *.py file in the examples/mylib directory run the ./flyde.py gen command to generate TS bindings
	@for file in $(LIB_DIR)/*.py; do \
		./flyde.py gen $$file; \
	done


test:
	@echo "Running tests..."
	@$(PYTHON) -m unittest discover -s $(TEST_DIR) -p "test_*.py";
