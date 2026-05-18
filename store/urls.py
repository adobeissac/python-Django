from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<str:cart_key>/', views.update_cart, name='update_cart'),
    path('cart/remove/<str:cart_key>/', views.remove_from_cart, name='remove_from_cart'),

    # Checkout
    path('checkout/', views.checkout, name='checkout'),
    path('order/<int:order_id>/confirmation/', views.order_confirmation, name='order_confirmation'),

    # Account
    path('account/', views.account, name='account'),
    path('account/order/<int:order_id>/', views.order_detail, name='order_detail'),

    # Auth
    path('accounts/register/', views.register, name='register'),
]
