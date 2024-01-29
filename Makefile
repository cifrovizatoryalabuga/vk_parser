clean_dev:
	rm -rf .venv/

develop: clean_dev
	python3.11 -m venv .venv
	.venv/bin/pip install -U pip poetry
	.venv/bin/poetry config virtualenvs.create false
	.venv/bin/poetry install

local:
	docker-compose -f docker-compose.dev.yaml up --force-recreate --renew-anon-volumes --build
