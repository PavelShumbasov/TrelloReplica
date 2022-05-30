# Dockerfile

# pull the official docker image
FROM python:3.9.4-slim

# set work directory
WORKDIR /app

# set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV POETRY_VERSION=1.1.12


RUN pip install "poetry==$POETRY_VERSION"


# set work directory
WORKDIR /app

COPY poetry.lock pyproject.toml /app/

RUN poetry config virtualenvs.create false
RUN poetry export -f requirements.txt --output requirements.txt
RUN pip install -r requirements.txt

# copy project
COPY . .
