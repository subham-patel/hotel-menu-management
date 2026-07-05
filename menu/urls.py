from django.urls import path
from . import views

urlpatterns = [
    path("", views.menu_view, name="menu_view"),
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
        "api/place-order/",
        views.PlaceOrderAPIView.as_view(),
        name="api_place_order",
    ),
]
