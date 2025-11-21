default:
  just --list

run *args:
  uvicorn services.app.main:app --reload {{args}}

ruff *args:
  ruff check {{args}} app

lint:
  ruff format app
  just ruff --fix

# docker
up:
  docker-compose up -d

kill *args:
  docker-compose kill {{args}}

build:
  docker-compose build

ps:
  docker-compose ps

pre-commit:
  git add .
  pre-commit run --all-files
