from django.urls import path
from . import views

urlpatterns = [
    path("", views.menu_view, name="menu_view"),
    path("qr-image/<int:table_id>/", views.qr_code_image_view, name="qr_code_image"),
    path(
        "api/categories/",
        views.CategoryListAPIView.as_view(),
        name="api_categories",
    ),
    path(
        "api/menu-items/",
        views.MenuItemListAPIView.as_view(),
        name="api_menu_items",
    ),
    path(
        "api/payment-methods/",
        views.PaymentMethodListAPIView.as_view(),
        name="api_payment_methods",
    ),
    path(
        "api/place-order/",
        views.PlaceOrderAPIView.as_view(),
        name="api_place_order",
    ),
    path(
        "api/orders/<str:order_id>/payment-method/",
        views.UpdateOrderPaymentMethodAPIView.as_view(),
        name="api_update_payment_method",
    ),
]
