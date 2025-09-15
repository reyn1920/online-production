.PHONY: install dev up down lint type test run

install:
	pip install --upgrade pip setuptools wheel
	pip install -r requirements.txt

dev:
	pip install -e .

up:
	docker compose -f infra/docker-compose.yml up -d

down:
	docker compose -f infra/docker-compose.yml down

lint:
	ruff check --fix .

type:
	pyright .

test:
	pytest -v

run:
	./run.sh
