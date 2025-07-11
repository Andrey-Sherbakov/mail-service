FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /mail-service

RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv sync --locked

COPY . .