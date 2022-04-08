#!/bin/bash

set -eo pipefail
shopt -s nullglob

# Formatting
if [ "$1" = "format" ]; then
    echo "formatting style..."
    black ./api ./db_adapters ./media_adapters
    isort ./api ./db_adapters ./media_adapters
    exit
fi

# Linting
if [ "$1" =  "lint" ]; then
    echo "Verifying style..."
    flake8 ./api ./db_adapters ./media_adapters # Plugins also verify isort and black
    exit
fi

# Database setup
if [ $DB_BACKEND = "POSTGRES" ]; then
  if [ -z ${PG_HOST+x} ]; then
    echo "PG_HOST needs to be defined!"
    exit
  fi
  echo "Upgrading the database..."
  cd ./db_adapters/postgres
  alembic upgrade head
  cd - > /dev/null
else if [ $DB_BACKEND = "DETA" ]; then
  if [ -z ${DETA_PROJECT_KEY+x} ]; then
    echo "DETA_PROJECT_KEY needs to be defined!"
    exit
  fi
fi
fi

if [ "$1" = "create_admin" ]; then
  echo "Creating an admin user..."
  python ./create_admin.py
else if [ "$1" = "serve" ]; then
    echo "Starting the API..."
    gunicorn -w $GUNICORN_WORKERS -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT --log-config logging.ini ${@:2} api.main:app
else
  exec "$@"
fi
fi
