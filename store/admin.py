from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.db.models import Sum

from .models import Category, Product, Order, OrderItem, UserProfile, Notification


# ---------------- CUSTOM ADMIN SITE ----------------

class CustomAdminSite(admin.AdminSite):
    site_header = "Smart Shop – Admin Dashboard"
    site_title = "Smart Shop Admin"
    index_title = "Business Overview"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        total_orders = Order.objects.count()
        total_users = UserProfile.objects.count()
        total_revenue = Order.objects.filter(
            payment_status='PAID'
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        order_status_count = {
            'PLACED': Order.objects.filter(status='PLACED').count(),
            'CONFIRMED': Order.objects.filter(status='CONFIRMED').count(),
            'SHIPPED': Order.objects.filter(status='SHIPPED').count(),
            'DELIVERED': Order.objects.filter(status='DELIVERED').count(),
            'CANCELLED': Order.objects.filter(status='CANCELLED').count(),
        }

        low_stock_products = Product.objects.filter(stock__lte=5)

        context = {
            'total_orders': total_orders,
            'total_users': total_users,
            'total_revenue': total_revenue,
            'order_status_count': order_status_count,
            'low_stock_products': low_stock_products,
        }

        return render(request, 'admin/dashboard.html', context)


# 🔑 CREATE ONE ADMIN SITE INSTANCE
custom_admin_site = CustomAdminSite(name='custom_admin')


# ---------------- ORDER ADMIN ACTIONS ----------------

def mark_confirmed(modeladmin, request, queryset):
    for order in queryset:
        order.status = 'CONFIRMED'
        order.save()
        Notification.objects.create(
            user=order.user,
            message=f"📦 Your Order #{order.id} has been confirmed"
        )

mark_confirmed.short_description = "Mark selected orders as Confirmed"


def mark_shipped(modeladmin, request, queryset):
    for order in queryset:
        order.status = 'SHIPPED'
        order.save()
        Notification.objects.create(
            user=order.user,
            message=f"🚚 Your Order #{order.id} has been shipped"
        )

mark_shipped.short_description = "Mark selected orders as Shipped"


def mark_delivered(modeladmin, request, queryset):
    for order in queryset:
        order.status = 'DELIVERED'
        order.save()
        Notification.objects.create(
            user=order.user,
            message=f"✅ Your Order #{order.id} has been delivered"
        )

mark_delivered.short_description = "Mark selected orders as Delivered"


# ---------------- ADMIN REGISTRATIONS ----------------

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'price', 'quantity')


@admin.register(Product, site=custom_admin_site)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock')
    list_filter = ('category',)
    search_fields = ('name',)


@admin.register(Order, site=custom_admin_site)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'status',
        'payment_method', 'payment_status',
        'total_amount', 'created_at'
    )
    list_filter = ('status', 'payment_method', 'payment_status')
    readonly_fields = ('payment_method', 'payment_status', 'total_amount', 'created_at')
    inlines = [OrderItemInline]
    actions = [mark_confirmed, mark_shipped, mark_delivered]


@admin.register(UserProfile, site=custom_admin_site)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone')


custom_admin_site.register(Category)
