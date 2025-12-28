from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'store'

urlpatterns = [

    # ================= AUTH =================
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # ================= HOME / PRODUCT =================
    path('', views.home, name='home'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    # ================= CART =================
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/<int:product_id>/<str:action>/', views.update_cart, name='update_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),

    # ================= CHECKOUT =================
    path('checkout/', views.checkout, name='checkout'),

    # ================= ORDERS =================
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('invoice/<int:order_id>/', views.invoice, name='invoice'),

    # ================= PROFILE & NOTIFICATIONS =================
    path('profile/', views.user_profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('notifications/', views.notifications_page, name='notifications'),
    path('notification/delete/<int:notification_id>/', views.delete_notification, name='delete_notification'),
    path('notification/clear/', views.clear_notifications, name='clear_notifications'),

    # ================= STATIC PAGES =================
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_and_conditions, name='terms'),
    path('shipping-policy/', views.shipping_policy, name='shipping_policy'),
    path('refund-policy/', views.refund_policy, name='refund_policy'),
    path('contact/', views.contact_page, name='contact'),
]

# ================= PASSWORD RESET (DJANGO BUILT-IN) =================

urlpatterns += [

    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='store/password_reset.html'
        ),
        name='password_reset'
    ),

    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='store/password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='store/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),

    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='store/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]
