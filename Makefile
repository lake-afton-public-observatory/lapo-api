.PHONY: install run test

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --reload --port 3333

test:
	python -m pytest tests/ -v
