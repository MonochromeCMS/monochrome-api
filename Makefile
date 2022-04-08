include .env

file ?= docker-compose.yml
buildkit ?= 1 # If buildkit should be used
test_exit ?= 0 # If a failed test should stop everything
user ?= `id -u`
dir ?= `pwd`

DOCKER_DEV = docker-compose -f $(file) run --rm -v "`pwd`:/mnt" -w "/mnt" api
DOCKER_DEV_BARE = docker-compose -f $(file) run --rm -v "`pwd`:/mnt" -w "/mnt" --entrypoint "" api

.PHONY: help
help: ## Show this help
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Docker specific commands

.PHONY: build
build:	## Build image
	DOCKER_BUILDKIT=$(buildkit) docker-compose build

.PHONY: up
.ONESHELL: up
up start:	## Run a container from the image
	docker-compose up -d

.PHONY: up
.ONESHELL: up
down stop:	## Stops the container running
	docker-compose down

.PHONY: logs
logs:	## Read the container's logs
	docker-compose logs -f --tail 500

.PHONY: sh
sh: ## Open a shell in the running container
	docker-compose exec api bash

.PHONY: secret
secret: ## Generate a secret
	@openssl rand -hex 30

.PHONY: create_admin
.ONESHELL: create_admin
create_admin: ## Create a new admin user
	docker-compose run --rm api create_admin

# Dev utils

.PHONY: lock
.ONESHELL: lock
lock:	## Refresh pipfile.lock
	@$(DOCKER_DEV_BARE) pipenv lock --pre

	$(DOCKER_DEV_BARE) bash -c "pipenv lock --pre -r > requirements.tmp.txt"
	tail +9 requirements.tmp.txt > requirements.txt
	rm -f requirements.tmp.txt
	sed -i "s/;.*$$//g" requirements.txt   

.PHONY: lint
lint:  ## Lint project code
ifneq ($(test_exit),0)
	$(DOCKER_DEV) lint
else
	-$(DOCKER_DEV) lint
endif

.PHONY: format
format:  ## Format project code
	$(DOCKER_DEV) format

# Postgres

.PHONY: revision
.ONESHELL: revision
revision rev: ## Create a new database revision
	@read -p "Revision name: " rev
	$(DOCKER_DEV_BARE) bash -c "cd db_adapters/postgres && alembic revision --autogenerate -m '$$rev'"

.PHONY: upgrade
.ONESHELL: upgrade
upgrade: ## Update the database
	$(DOCKER_DEV_BARE) bash -c "cd db_adapters/postgres && alembic upgrade head"

.PHONY: downgrade
downgrade: ## Downgrade the database
	$(DOCKER_DEV_BARE) bash -c "cd db_adapters/postgres && alembic downgrade -1"
