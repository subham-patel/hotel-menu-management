import base64
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from .models import Category, MenuItem, PaymentMethod, Order, Table
from .serializers import CategorySerializer, MenuItemSerializer, PaymentMethodSerializer, CreateOrderSerializer


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


def qr_code_image_view(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    if not table.qr_code_data:
        raise Http404("QR code not available")
    image_data = base64.b64decode(table.qr_code_data)
    return HttpResponse(image_data, content_type="image/png")


class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.prefetch_related("items").all()
    serializer_class = CategorySerializer


class MenuItemListAPIView(generics.ListAPIView):
    queryset = MenuItem.objects.filter(available=True)
    serializer_class = MenuItemSerializer


class PaymentMethodListAPIView(generics.ListAPIView):
    queryset = PaymentMethod.objects.filter(is_active=True)
    serializer_class = PaymentMethodSerializer


class PlaceOrderAPIView(generics.CreateAPIView):
    serializer_class = CreateOrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        payment_method = None
        if order.payment_method:
            payment_method = {
                "code": order.payment_method.code,
                "name": order.payment_method.name,
            }
        return Response(
            {
                "success": True,
                "order_id": order.order_id,
                "total": str(order.total),
                "payment_method": payment_method,
                "message": f"Order {order.order_id} placed successfully!",
            },
            status=status.HTTP_201_CREATED,
        )


class UpdateOrderPaymentMethodAPIView(generics.UpdateAPIView):
    queryset = Order.objects.all()
    lookup_field = "order_id"

    def patch(self, request, *args, **kwargs):
        order = self.get_object()
        code = request.data.get("payment_method_code")
        if not code:
            return Response(
                {"error": "payment_method_code is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            method = PaymentMethod.objects.get(code=code, is_active=True)
        except PaymentMethod.DoesNotExist:
            return Response(
                {"error": f"Payment method '{code}' is not available."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.payment_method = method
        order.save(update_fields=["payment_method"])
        return Response(
            {
                "success": True,
                "order_id": order.order_id,
                "payment_method": {"code": method.code, "name": method.name},
            }
        )
