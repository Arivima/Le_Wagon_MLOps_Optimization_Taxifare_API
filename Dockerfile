# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY pyproject.toml /app/
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev


COPY . .

CMD ["poetry", "run", "gunicorn", \
     "-w", "2", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "app.main:app", \
     "--bind", "0.0.0.0:8080"]
