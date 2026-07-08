from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.http import HttpResponse
import base64
from .models import Category, MenuItem, Table, Order, OrderItem, PaymentMethod


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "order"]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "available", "image_preview"]
    list_filter = ["category", "available"]
    list_editable = ["available"]
    readonly_fields = ["image_preview"]
    fieldsets = [
        (None, {
            "fields": ["category", "name", "description", "price", "available"],
        }),
        ("Image", {
            "fields": ["image", "image_preview"],
        }),
    ]

    def image_preview(self, obj):
        try:
            if obj.image and obj.image.storage.exists(obj.image.name):
                return mark_safe(f'<img src="{obj.image.url}" width="120" style="border-radius:8px;object-fit:cover" />')
            return mark_safe('<span style="color:#999">No image uploaded</span>')
        except Exception:
            return mark_safe('<span style="color:#999">Image unavailable</span>')

    image_preview.short_description = "Preview"


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ["number", "qr_code_preview", "created_at"]
    readonly_fields = ["qr_code", "qr_code_data"]
    actions = ["regenerate_qr_codes"]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:table_id>/regenerate-qr/",
                self.admin_site.admin_view(self.regenerate_single_qr),
                name="menu_table_regenerate_qr",
            ),
            path(
                "<int:table_id>/download-qr/",
                self.admin_site.admin_view(self.download_qr),
                name="menu_table_download_qr",
            ),
        ]
        return custom_urls + urls

    def regenerate_single_qr(self, request, table_id):
        table = Table.objects.get(id=table_id)
        table.generate_qr_code()
        self.message_user(request, f"QR code regenerated for Table {table.number}.", messages.SUCCESS)
        return redirect(request.META.get("HTTP_REFERER", "admin:menu_table_changelist"))

    def download_qr(self, request, table_id):
        table = Table.objects.get(id=table_id)
        if not table.qr_code_data:
            self.message_user(request, f"No QR code available for Table {table.number}.", messages.ERROR)
            return redirect(request.META.get("HTTP_REFERER", "admin:menu_table_changelist"))
        img_data = base64.b64decode(table.qr_code_data)
        response = HttpResponse(img_data, content_type="image/png")
        response["Content-Disposition"] = f'attachment; filename="table_{table.number}_qr.png"'
        return response

    @admin.action(description="Regenerate QR codes for selected tables")
    def regenerate_qr_codes(self, request, queryset):
        count = 0
        for table in queryset:
            table.generate_qr_code()
            count += 1
        self.message_user(request, f"Regenerated QR codes for {count} table(s).", messages.SUCCESS)

    def qr_code_preview(self, obj):
        try:
            if obj.qr_code_data:
                img = f'data:image/png;base64,{obj.qr_code_data}'
            elif obj.qr_code and obj.qr_code.storage.exists(obj.qr_code.name):
                img = obj.qr_code.url
            else:
                return mark_safe(
                    '<span style="color:#999">QR unavailable</span>'
                    f'<br><a href="../{obj.id}/regenerate-qr/" style="font-size:0.75rem">Generate</a>'
                )
            return mark_safe(
                f'<img src="{img}" width="100" height="100" style="display:block;margin-bottom:4px" />'
                f'<a href="../{obj.id}/download-qr/" style="font-size:0.75rem">⬇ Download</a> | '
                f'<a href="../{obj.id}/regenerate-qr/" style="font-size:0.75rem" '
                f'onclick="return confirm(\'Regenerate QR code for Table {obj.number}?\')">🔄 Regenerate</a>'
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
        "phone",
        "status",
        "payment_method",
        "utrn_display",
        "payment_verified",
        "subtotal",
        "gst_display",
        "total",
        "created_at",
    ]
    list_filter = ["status", "payment_method", "payment_verified", "created_at"]
    list_editable = ["status", "payment_verified"]
    inlines = [OrderItemInline]
    readonly_fields = ["order_id", "subtotal", "gst_amount", "total"]
    fieldsets = [
        (None, {
            "fields": ["order_id", "table", "phone", "status", "note"],
        }),
        ("Billing", {
            "fields": ["subtotal", "gst_amount", "total"],
        }),
        ("Payment", {
            "fields": ["payment_method", "utrn", "payment_verified"],
        }),
    ]

    def gst_display(self, obj):
        return f"₹{obj.gst_amount:.2f}"
    gst_display.short_description = "GST (5%)"

    def utrn_display(self, obj):
        return obj.utrn if obj.utrn else "—"
    utrn_display.short_description = "UTRN"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["subtitle"] = mark_safe(
            '<script>setTimeout(function(){ window.location.reload(); }, 10000);</script>'
        )
        return super().changelist_view(request, extra_context=extra_context)
