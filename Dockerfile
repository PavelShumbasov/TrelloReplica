# Dockerfile

# pull the official docker image
FROM python:3.9.4-slim

# set work directory
WORKDIR /app

# set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
COPY requirements.txt .
#COPY poetry.lock pyproject.toml /app/
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# copy project
COPY . .
