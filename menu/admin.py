from django.contrib import admin
from django.template.response import TemplateResponse
from .models import Category, MenuItem, Table, Order, OrderItem


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
        if obj.qr_code:
            return f'<img src="{obj.qr_code.url}" width="100" height="100" />'
        return "—"

    qr_code_preview.allow_tags = True
    qr_code_preview.short_description = "QR Code"


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
        "total",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    list_editable = ["status"]
    inlines = [OrderItemInline]
    readonly_fields = ["order_id", "total"]

    def changelist_view(self, request, extra_context=None):
        resp = super().changelist_view(request, extra_context)
        if isinstance(resp, TemplateResponse):
            resp.add_post_render_callback(
                lambda r: r.content.replace(
                    b"</head>",
                    b'<meta http-equiv="refresh" content="10"></head>',
                )
            )
        return resp
