FROM python:3.11-slim

RUN pip install -U pip poetry && poetry config virtualenvs.create false

WORKDIR /app

COPY ./pyproject.toml ./poetry.lock* /app/
RUN poetry install --no-interaction --no-ansi --without dev

COPY ./vk_parser /app/vk_parser

ENV PYTHONPATH=/app

ENTRYPOINT [ "python", "-m" "vk_parser.db", "upgrade", "head" ]
