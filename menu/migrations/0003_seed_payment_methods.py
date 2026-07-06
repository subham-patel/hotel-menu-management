from django.db import migrations


def seed_payment_methods(apps, schema_editor):
    PaymentMethod = apps.get_model("menu", "PaymentMethod")
    PaymentMethod.objects.get_or_create(
        code="cash",
        defaults={
            "name": "Pay by Cash",
            "description": "Pay at the restaurant counter",
            "is_active": True,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0002_paymentmethod_order_payment_method'),
    ]

    operations = [
        migrations.RunPython(seed_payment_methods, migrations.RunPython.noop),
    ]
