from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    path('', views.home, name='home'),
    path('category/<slug:slug>/', views.category_products, name='category_products'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/<int:product_id>/<str:action>/', views.update_cart, name='update_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),

    path('checkout/', views.checkout, name='checkout'),
    path('payment-success/', views.payment_success, name='payment_success'),

    path('my-orders/', views.my_orders, name='my_orders'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('invoice/<int:order_id>/', views.invoice, name='invoice'),

    path('profile/', views.user_profile, name='profile'),

    # 🔔 NOTIFICATIONS (PHASE 9)
    path('notifications/', views.notifications_page, name='notifications'),
    path('notification/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notification/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),

    path('notification/delete/<int:notification_id>/', views.delete_notification, name='delete_notification'),
    path('notification/clear/', views.clear_notifications, name='clear_notifications'),

    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_and_conditions, name='terms'),
    path('shipping-policy/', views.shipping_policy, name='shipping_policy'),
    path('refund-policy/', views.refund_policy, name='refund_policy'),
    path('contact/', views.contact_page, name='contact'),
]
