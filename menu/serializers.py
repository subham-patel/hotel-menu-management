from rest_framework import serializers
from django.conf import settings
from .models import Category, MenuItem, Table, Order, OrderItem, PaymentMethod


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ["id", "name", "description", "price", "image", "available"]


class CategorySerializer(serializers.ModelSerializer):
    items = MenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "items"]


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "menu_item", "item_name", "quantity", "unit_price"]


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ["id", "name", "code", "description", "upi_id", "upi_qr_code"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payment_method = PaymentMethodSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_id",
            "table",
            "status",
            "note",
            "subtotal",
            "gst_amount",
            "total",
            "phone",
            "items",
            "payment_method",
            "created_at",
        ]


class CreateOrderItemSerializer(serializers.Serializer):
    menu_item_id = serializers.IntegerField()
    item_name = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=8, decimal_places=2)


class CreateOrderSerializer(serializers.Serializer):
    table_number = serializers.IntegerField()
    note = serializers.CharField(required=False, allow_blank=True)
    items = CreateOrderItemSerializer(many=True)
    payment_method_code = serializers.CharField(required=False, allow_blank=True)
    utrn = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)

    def validate_table_number(self, value):
        if not Table.objects.filter(number=value).exists():
            raise serializers.ValidationError(f"Table {value} does not exist.")
        return value

    def validate_payment_method_code(self, value):
        if value:
            if not PaymentMethod.objects.filter(code=value, is_active=True).exists():
                raise serializers.ValidationError(f"Payment method '{value}' is not available.")
        return value

    def create(self, validated_data):
        table = Table.objects.get(number=validated_data["table_number"])
        items_data = validated_data.pop("items")
        note = validated_data.pop("note", "")
        payment_method_code = validated_data.pop("payment_method_code", None)
        utrn = validated_data.pop("utrn", "")
        phone = validated_data.pop("phone", "")

        payment_method = None
        if payment_method_code:
            payment_method = PaymentMethod.objects.get(code=payment_method_code)

        order = Order.objects.create(
            table=table, note=note, payment_method=payment_method,
            utrn=utrn, phone=phone,
        )

        subtotal = 0
        order_items = []
        for item_data in items_data:
            unit_price = item_data["unit_price"]
            quantity = item_data["quantity"]
            line_total = unit_price * quantity
            subtotal += line_total
            order_items.append(
                OrderItem(
                    order=order,
                    menu_item_id=item_data["menu_item_id"],
                    item_name=item_data["item_name"],
                    quantity=quantity,
                    unit_price=unit_price,
                )
            )
        OrderItem.objects.bulk_create(order_items)

        gst_amount = round(subtotal * settings.GST_RATE, 2)
        total = subtotal + gst_amount
        order.subtotal = subtotal
        order.total = total
        order.gst_amount = gst_amount
        order.save(update_fields=["subtotal", "total", "gst_amount"])
        return order
