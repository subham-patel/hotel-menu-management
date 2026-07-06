from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Automatically creates a superuser on Render using environment variables'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Render ke environment variables se username, email aur password read karenge
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin@1234')

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username,password=password)
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully!'))
        else:
            self.stdout.write(self.style.WARNING(f'Superuser "{username}" already exists.'))