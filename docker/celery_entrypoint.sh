#!/bin/sh
set -o errexit
set -o nounset

uv run celery -A src.app.worker:celery_app worker -l info