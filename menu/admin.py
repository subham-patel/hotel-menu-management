from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Category, MenuItem, Table, Order, OrderItem, PaymentMethod


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "order"]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "available"]
    list_filter = ["category", "available"]
    list_editable = ["available"]


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ["number", "qr_code_preview", "created_at"]
    readonly_fields = ["qr_code"]

    def qr_code_preview(self, obj):
        try:
            if obj.qr_code and obj.qr_code.storage.exists(obj.qr_code.name):
                return f'<img src="{obj.qr_code.url}" width="100" height="100" />'
        except Exception:
            pass
        return "—"

    qr_code_preview.allow_tags = True
    qr_code_preview.short_description = "QR Code"


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "upi_id", "is_active", "created_at"]
    list_editable = ["is_active"]
    prepopulated_fields = {"code": ("name",)}
    fieldsets = [
        (None, {"fields": ["name", "code", "description", "is_active"]}),
        ("UPI Settings", {
            "fields": ["upi_id", "upi_qr_code"],
            "classes": ["collapse"],
            "description": "Configure UPI payment details. Only applicable if this is a UPI payment method.",
        }),
    ]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["menu_item", "item_name", "quantity", "unit_price"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "order_id",
        "table",
        "status",
        "payment_method",
        "total",
        "created_at",
    ]
    list_filter = ["status", "payment_method", "created_at"]
    list_editable = ["status"]
    inlines = [OrderItemInline]
    readonly_fields = ["order_id", "total"]

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["subtitle"] = mark_safe(
            '<script>setTimeout(function(){ window.location.reload(); }, 10000);</script>'
        )
        return super().changelist_view(request, extra_context=extra_context)
