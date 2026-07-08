import uuid
import qrcode
from io import BytesIO
from django.db import models
from django.core.files.base import ContentFile
from django.urls import reverse
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["order"]

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="items"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to="menu_images/", blank=True, null=True)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Table(models.Model):
    number = models.IntegerField(unique=True, verbose_name="Table Number")
    qr_code = models.ImageField(upload_to="qr_codes/", blank=True, null=True, editable=False)
    qr_code_data = models.TextField(blank=True, editable=False, help_text="Base64-encoded QR code image (permanent storage)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"Table {self.number}"

    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)
        if is_new or not self.qr_code_data:
            self.generate_qr_code()

    def generate_qr_code(self):
        domain = settings.SITE_DOMAIN.rstrip('/')
        menu_url = f"{domain}{reverse('menu_view')}?table={self.number}"
        
        qr = qrcode.make(menu_url, box_size=10, border=4)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        import base64
        self.qr_code_data = base64.b64encode(buffer.getvalue()).decode()
        filename = f"table_{self.number}.png"
        self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
        self.save(update_fields=["qr_code", "qr_code_data"])

    @property
    def qr_code_image_url(self):
        if self.qr_code_data:
            return f"data:image/png;base64,{self.qr_code_data}"
        return ""


class PaymentMethod(models.Model):
    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=50, unique=True, help_text="Unique identifier (e.g., 'cash', 'card', 'upi')")
    description = models.TextField(blank=True)
    upi_id = models.CharField(max_length=100, blank=True, help_text="UPI ID (e.g., restaurant@upi)")
    upi_qr_code = models.ImageField(upload_to="upi_qr_codes/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("preparing", "Preparing"),
        ("ready", "Ready"),
        ("served", "Served"),
        ("cancelled", "Cancelled"),
    ]

    table = models.ForeignKey(
        Table, on_delete=models.CASCADE, related_name="orders"
    )
    order_id = models.CharField(max_length=12, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    note = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    gst_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    phone = models.CharField(max_length=15, blank=True, verbose_name="Mobile Number")
    payment_method = models.ForeignKey(
        PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )
    utrn = models.CharField(max_length=50, blank=True, verbose_name="UPI Transaction Reference")
    payment_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.order_id} – Table {self.table.number}"

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items"
    )
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True)
    item_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.item_name}"