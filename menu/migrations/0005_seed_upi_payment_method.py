from django.db import migrations


def seed_upi_method(apps, schema_editor):
    PaymentMethod = apps.get_model("menu", "PaymentMethod")
    PaymentMethod.objects.get_or_create(
        code="upi",
        defaults={
            "name": "Pay by UPI",
            "description": "Pay using any UPI app (Google Pay, PhonePe, Paytm)",
            "upi_id": "restaurant@upi",
            "is_active": True,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0004_paymentmethod_upi_id_paymentmethod_upi_qr_code'),
    ]

    operations = [
        migrations.RunPython(seed_upi_method, migrations.RunPython.noop),
    ]
