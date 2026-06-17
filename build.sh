#!/usr/bin/env bash
# Exit immediately if any command exits with a non-zero status
set -o errexit

# Install python dependencies
pip install -r requirements.txt

# Gather all static assets into STATIC_ROOT
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate
