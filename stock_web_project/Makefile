.PHONY: install run test compile

PYTHON ?= python3

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) run.py

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py" -v

compile:
	$(PYTHON) -m compileall stock_web_app run.py
