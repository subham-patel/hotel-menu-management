from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from .models import Category, MenuItem
from .serializers import CategorySerializer, MenuItemSerializer, CreateOrderSerializer


def menu_view(request):
    categories = Category.objects.prefetch_related("items").all()
    table_number = request.GET.get("table", "")
    context = {
        "categories": categories,
        "table_number": table_number,
        "restaurant_name": "The Grand",
        "restaurant_suffix": "Kitchen",
    }
    return render(request, "menu/menu.html", context)


class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.prefetch_related("items").all()
    serializer_class = CategorySerializer


class MenuItemListAPIView(generics.ListAPIView):
    queryset = MenuItem.objects.filter(available=True)
    serializer_class = MenuItemSerializer


class PlaceOrderAPIView(generics.CreateAPIView):
    serializer_class = CreateOrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(
            {
                "success": True,
                "order_id": order.order_id,
                "total": str(order.total),
                "message": f"Order {order.order_id} placed successfully!",
            },
            status=status.HTTP_201_CREATED,
        )
