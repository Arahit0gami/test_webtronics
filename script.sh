#!/bin/bash
set -e
docker build -t myapp:v01 .
docker compose -f ./tests/docker-compose.yml --env-file ./.env up --exit-code-from test-app
docker compose -f ./tests/docker-compose.yml down
docker compose up --wait
docker exec prod-app alembic upgrade head
