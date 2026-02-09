#!/bin/sh
set -o errexit
set -o nounset

uv run celery -A app.worker:celery_app worker -l info -c 1