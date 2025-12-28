import razorpay
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q

from .models import (
    Category, Product, Order, OrderItem,
    UserProfile, Notification
)

razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

# ================= AUTH =================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('store:home')

    if request.method == 'POST':
        identifier = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user_obj = User.objects.get(
                Q(username=identifier) | Q(email=identifier)
            )
            user = authenticate(
                request,
                username=user_obj.username,
                password=password
            )
        except User.DoesNotExist:
            user = None

        if user:
            login(request, user)
            return redirect('store:home')

        return render(request, 'store/login.html', {
            'error': 'Invalid credentials'
        })

    return render(request, 'store/login.html')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(
            Q(username=username) | Q(email=email)
        ).exists():
            return render(request, 'store/register.html', {
                'error': 'User already exists'
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        UserProfile.objects.create(user=user)
        return redirect('store:login')

    return render(request, 'store/register.html')


def logout_view(request):
    logout(request)
    return redirect('store:login')


# ================= HOME =================

@login_required
def home(request):
    return render(request, 'store/home.html', {
        'categories': Category.objects.all(),
        'products': Product.objects.all()
    })


# ================= CATEGORY =================

@login_required
def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    return render(request, 'store/category_products.html', {
        'category': category,
        'products': products
    })


# ================= PRODUCT =================

@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'store/product_detail.html', {
        'product': product
    })


# ================= CART =================

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if product.stock <= 0:
        return redirect('store:product_detail', product_id=product.id)

    cart = request.session.get('cart', {})
    pid = str(product_id)

    if request.GET.get('buy_now'):
        request.session['cart'] = {pid: 1}
        return redirect('store:checkout')

    cart[pid] = min(cart.get(pid, 0) + 1, product.stock)
    request.session['cart'] = cart
    return redirect('store:cart')


@login_required
def update_cart(request, product_id, action):
    cart = request.session.get('cart', {})
    pid = str(product_id)
    product = get_object_or_404(Product, id=product_id)

    if pid in cart:
        if action == 'increase' and cart[pid] < product.stock:
            cart[pid] += 1
        elif action == 'decrease':
            cart[pid] -= 1
            if cart[pid] <= 0:
                del cart[pid]

    request.session['cart'] = cart
    return redirect('store:cart')


@login_required
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart.pop(str(product_id), None)
    request.session['cart'] = cart
    return redirect('store:cart')


@login_required
def cart_view(request):
    cart = request.session.get('cart', {})
    items = []
    total = 0

    for pid, qty in cart.items():
        product = get_object_or_404(Product, id=pid)
        subtotal = product.price * qty
        total += subtotal
        items.append({
            'product': product,
            'quantity': qty,
            'subtotal': subtotal
        })

    return render(request, 'store/cart.html', {
        'cart_items': items,
        'total': total
    })


# ================= CHECKOUT =================

@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('store:cart')

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    total = 0
    items = []

    for pid, qty in cart.items():
        product = get_object_or_404(Product, id=pid)
        total += product.price * qty
        items.append((product, qty))

    if request.method == 'POST':
        address = request.POST.get('address')
        method = request.POST.get('payment_method')

        profile.address = address
        profile.save()

        if method == 'ONLINE':
            request.session['order_address'] = address
            return redirect('store:payment_success')

        order = Order.objects.create(
            user=request.user,
            address=address,
            total_amount=total,
            payment_method='COD',
            payment_status='PENDING',
            status='PLACED'
        )

        for product, qty in items:
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=qty,
                price=product.price
            )
            product.stock -= qty
            product.save()

        Notification.objects.create(
            user=request.user,
            message=f"✅ Order #{order.id} placed successfully"
        )

        request.session['cart'] = {}
        return redirect('store:invoice', order_id=order.id)

    return render(request, 'store/checkout.html', {'total': total})


# ================= PAYMENT SUCCESS =================

@login_required
def payment_success(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('store:home')

    address = request.session.get('order_address', '')
    total = 0
    items = []

    for pid, qty in cart.items():
        product = get_object_or_404(Product, id=pid)
        total += product.price * qty
        items.append((product, qty))

    order = Order.objects.create(
        user=request.user,
        address=address,
        total_amount=total,
        payment_method='ONLINE',
        payment_status='PAID',
        status='PLACED'
    )

    for product, qty in items:
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=qty,
            price=product.price
        )
        product.stock -= qty
        product.save()

    Notification.objects.create(
        user=request.user,
        message=f"💳 Online payment successful for Order #{order.id}"
    )

    request.session['cart'] = {}
    request.session.pop('order_address', None)

    return redirect('store:invoice', order_id=order.id)


# ================= ORDERS =================

@login_required
def my_orders(request):
    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'store/my_orders.html', {
        'orders': orders
    })


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )
    return render(request, 'store/order_detail.html', {
        'order': order
    })


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    if order.can_cancel():
        order.status = 'CANCELLED'
        order.save()

        Notification.objects.create(
            user=request.user,
            message=f"❌ Order #{order.id} cancelled"
        )

    return redirect('store:my_orders')


@login_required
def invoice(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )
    return render(request, 'store/invoice.html', {
        'order': order
    })


# ================= PROFILE (PHASE 12 ENHANCED) =================

@login_required
def user_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        request.user.email = request.POST.get('email')
        profile.phone = request.POST.get('phone')
        profile.address = request.POST.get('address')

        request.user.save()
        profile.save()

        return redirect('store:profile')

    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)

    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'store/profile.html', {
        'profile': profile,
        'notifications': notifications
    })


# ================= NOTIFICATIONS =================

@login_required
def notifications_page(request):
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'store/notifications.html', {
        'notifications': notifications
    })


@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    notification.is_read = True
    notification.save()
    return redirect('store:notifications')


@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)
    return redirect('store:notifications')


@login_required
def delete_notification(request, notification_id):
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    notification.delete()
    return redirect('store:profile')


@login_required
def clear_notifications(request):
    Notification.objects.filter(
        user=request.user
    ).delete()
    return redirect('store:profile')


# ================= STATIC =================

def privacy_policy(request):
    return render(request, 'store/privacy_policy.html')


def terms_and_conditions(request):
    return render(request, 'store/terms.html')


def shipping_policy(request):
    return render(request, 'store/shipping_policy.html')


def refund_policy(request):
    return render(request, 'store/refund_policy.html')


def contact_page(request):
    return render(request, 'store/contact.html')
