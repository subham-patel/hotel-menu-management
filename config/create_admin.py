import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

# Apna purana username aur password yahan likhein
USERNAME = 'apna_local_username' 
PASSWORD = 'apna_local_password'
EMAIL = 'admin@example.com'

if not User.objects.filter(username=USERNAME).exists():
    print("Creating superuser...")
    User.objects.create_superuser(USERNAME, EMAIL, PASSWORD)
    print("Superuser created successfully!")
else:
    print("Superuser already exists.")