#!/bin/sh
set -e

echo "Running migrations..."
uv run alembic upgrade head

echo "Downloading models..."
uv run python scripts/hf_models.py

echo "Seeding roles..."
uv run python scripts/seeder/role_seed.py

echo "Seeding admin..."
uv run python scripts/seeder/admin_seed.py

echo "Starting app..."
exec uv run python src/app/main.py