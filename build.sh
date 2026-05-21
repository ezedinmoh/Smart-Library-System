#!/usr/bin/env bash
# Render build script

set -o errexit  # Exit on error

pip install -r requirements.txt

python manage.py collectstatic --no-input --settings=library_system.settings_production

python manage.py migrate --settings=library_system.settings_production

python manage.py generate_qr_codes --settings=library_system.settings_production
