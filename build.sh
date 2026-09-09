#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# Remove existing staticfiles directory to prevent broken cache issues
rm -rf staticfiles

# Collect static files using standard Django collector
python manage.py collectstatic --no-input --clear
python manage.py migrate

# Auto-create superuser
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'AdminPass123!')
    print('Superuser created successfully!')
"