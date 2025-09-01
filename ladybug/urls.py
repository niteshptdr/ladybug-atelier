from django.urls import path
from . import views
from django.views.generic.base import RedirectView

urlpatterns = [
    path('', views.home, name='home'),
    path('select-category', views.select_category, name='select-category'),
    path('select-fabric-option', views.select_fabric_option, name='select-fabric-option'),
    path('select-pickup-option', views.select_pickup_option, name='select-pickup-option'),

    path('select-fabric', views.select_fabric, name='select-fabric'),
    path('get-similar-products/', views.get_similar_products, name='get-similar-products'),
    path('get-similar-products-pattern/', views.get_similar_products_pattern, name='get-similar-products-pattern'),

    path('select-style', views.select_style, name='select-style'),
    path('measurements', views.measurements, name='measurements'),
    path('options', views.options, name='options'),
    path('register', views.register, name = 'register'),
    path('login', views.login_otp, name = 'login'),
    path('logout', views.user_logout, name = 'logout'),
    # path('register/<str:mobile>/mobile-authentication/', views.verify_otp, name = 'verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend-otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('cart', views.user_cart, name = 'cart'),
    path('orders', views.orders, name = 'orders'),
    path('address', views.address, name = 'address'),
    path('order-review', views.order_review, name = 'order-review'),
    path('order-success', views.order_success, name = 'order-success'),

    path('products', views.products, name='products'),
    path('<str:product_id>/product-detail', views.product_detail, name= 'product-detail'),
    path('<str:product_id>/product-measurements', views.product_measurements, name= 'product-measurements'),
    path('submit_review/<str:review_token>/', views.submit_review, name='submit_review'),
    path('thankyou', views.thankyou, name = 'thankyou'),
    path('review_exists', views.review_exists, name = 'review_exists'),
    path('error_page', views.error_page, name = 'error_page'),

    path('manual-order', views.admin_create_order, name='admin-create-order'),
    path('manual-order/lookup-customer/', views.lookup_customer_by_mobile, name='lookup-customer'),
    path("<int:order_id>/invoice/", views.admin_order_invoice, name="admin_order_invoice"),


    path("links/", views.LinksView, name="links"),  # <-- name added
    path("dev/", views.dev, name="dev"),  # <-- name added

]