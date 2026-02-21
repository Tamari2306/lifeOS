#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input --settings=backend.settings_production
python manage.py migrate --settings=backend.settings_production