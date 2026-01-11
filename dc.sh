#!/bin/bash
# Convenience wrapper for docker compose with .env.local
# Usage: ./dc.sh [docker-compose-args]
# Examples:
#   ./dc.sh up -d
#   ./dc.sh down
#   ./dc.sh logs -f web
#   ./dc.sh exec web python manage.py migrate

docker compose --env-file deploy/.env.local -f deploy/docker-compose.yml "$@"

