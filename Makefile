PYTHON = python3
MAP ?= maps/easy/01_linear_path.txt
F = flake8 .
MY = mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

install:
	@echo "No dependencies to install"

run:
	@$(PYTHON) main.py $(MAP)

debug:
	@$(PYTHON) -m pdb main.py $(MAP)

clean:
	@rm -rf __pycache__ .mypy_cache .pytest_cache

lint:
	@$(F)
	@$(MY)
