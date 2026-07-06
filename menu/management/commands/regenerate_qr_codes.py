from django.core.management.base import BaseCommand
from menu.models import Table


class Command(BaseCommand):
    help = "Regenerate QR codes for all tables where the file is missing"

    def handle(self, *args, **options):
        tables = Table.objects.all()
        regenerated = 0
        for table in tables:
            if not table.qr_code or not table.qr_code.storage.exists(table.qr_code.name):
                table.generate_qr_code()
                regenerated += 1
                self.stdout.write(f"  Regenerated QR code for Table {table.number}")
        if regenerated:
            self.stdout.write(self.style.SUCCESS(f"Regenerated {regenerated} QR code(s)"))
        else:
            self.stdout.write("All QR codes exist. Nothing to regenerate.")
