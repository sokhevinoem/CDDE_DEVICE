#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# បង្កើត Superuser ដោយស្វ័យប្រវត្តិ
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='kevin').exists():
    User.objects.create_superuser('kevin', 'admin@example.com', 'Admin123')
    print('Superuser created successfully!')
"