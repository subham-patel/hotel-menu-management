from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.contrib import messages
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
    actions = ["regenerate_qr_codes"]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:table_id>/regenerate-qr/",
                self.admin_site.admin_view(self.regenerate_single_qr),
                name="menu_table_regenerate_qr",
            ),
        ]
        return custom_urls + urls

    def regenerate_single_qr(self, request, table_id):
        table = Table.objects.get(id=table_id)
        table.generate_qr_code()
        self.message_user(request, f"QR code regenerated for Table {table.number}.", messages.SUCCESS)
        return redirect(request.META.get("HTTP_REFERER", "admin:menu_table_changelist"))

    @admin.action(description="Regenerate QR codes for selected tables")
    def regenerate_qr_codes(self, request, queryset):
        count = 0
        for table in queryset:
            table.generate_qr_code()
            count += 1
        self.message_user(request, f"Regenerated QR codes for {count} table(s).", messages.SUCCESS)

    def qr_code_preview(self, obj):
        try:
            if obj.qr_code and obj.qr_code.storage.exists(obj.qr_code.name):
                img = f'<img src="{obj.qr_code.url}" width="100" height="100" style="display:block;margin-bottom:4px" />'
            else:
                img = '<span style="color:#999">File missing</span>'
            url = f"../{obj.id}/regenerate-qr/"
            return mark_safe(
                f'{img}<a href="{url}" style="font-size:0.75rem" onclick="return confirm(\'Regenerate QR code for Table {obj.number}? This will update the QR image.\')">🔄 Regenerate</a>'
            )
        except Exception:
            return mark_safe("—")

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
