from rest_framework import serializers
from .models import Category, MenuItem, Table, Order, OrderItem


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


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_id",
            "table",
            "status",
            "note",
            "total",
            "items",
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

    def validate_table_number(self, value):
        if not Table.objects.filter(number=value).exists():
            raise serializers.ValidationError(f"Table {value} does not exist.")
        return value

    def create(self, validated_data):
        table = Table.objects.get(number=validated_data["table_number"])
        items_data = validated_data.pop("items")
        note = validated_data.pop("note", "")

        order = Order.objects.create(table=table, note=note)

        total = 0
        order_items = []
        for item_data in items_data:
            unit_price = item_data["unit_price"]
            quantity = item_data["quantity"]
            line_total = unit_price * quantity
            total += line_total
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
        order.total = total
        order.save(update_fields=["total"])
        return order
