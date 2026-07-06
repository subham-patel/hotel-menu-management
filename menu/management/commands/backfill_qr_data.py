from django.core.management.base import BaseCommand
from menu.models import Table


class Command(BaseCommand):
    help = "Backfill qr_code_data for existing tables that have a QR file but no base64 data"

    def handle(self, *args, **options):
        tables = Table.objects.filter(qr_code_data="")
        count = 0
        for table in tables:
            if table.qr_code and table.qr_code.storage.exists(table.qr_code.name):
                with table.qr_code.open("rb") as f:
                    import base64
                    table.qr_code_data = base64.b64encode(f.read()).decode()
                    table.save(update_fields=["qr_code_data"])
                    count += 1
                    self.stdout.write(f"  Backfilled QR data for Table {table.number}")
        if count:
            self.stdout.write(self.style.SUCCESS(f"Backfilled {count} table(s)"))
        else:
            self.stdout.write("No tables need backfilling.")
