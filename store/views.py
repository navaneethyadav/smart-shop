import uuid

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.core.mail import send_mail
from django.urls import reverse

from .models import (
    Product,
    Order,
    OrderItem,
    UserProfile,
    Notification,
    EmailVerificationToken
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
        except User.DoesNotExist:
            return render(request, 'store/login.html', {
                'error': 'Invalid credentials'
            })

        if not user_obj.is_active:
            return render(request, 'store/login.html', {
                'error': 'Please verify your email before logging in'
            })

        user = authenticate(
            request,
            username=user_obj.username,
            password=password
        )

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

        if User.objects.filter(Q(username=username) | Q(email=email)).exists():
            return render(request, 'store/register.html', {
                'error': 'User already exists'
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=False
        )

        UserProfile.objects.create(user=user)

        token = EmailVerificationToken.objects.create(user=user)

        verification_link = request.build_absolute_uri(
            reverse('store:verify_email', args=[token.token])
        )

        send_mail(
            subject='Verify your Smart Shop account',
            message=f"""
Hello {user.username},

Please verify your email by clicking the link below:

{verification_link}

If you didn’t register, ignore this email.

– Smart Shop Team
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )

        return render(request, 'store/register_success.html')

    return render(request, 'store/register.html')


def verify_email(request, token):
    token_obj = get_object_or_404(EmailVerificationToken, token=token)
    user = token_obj.user

    user.is_active = True
    user.save()

    token_obj.delete()

    return render(request, 'store/email_verified.html')


def logout_view(request):
    logout(request)
    return redirect('store:login')


# ================= HOME =================

@login_required
def home(request):
    return render(request, 'store/home.html', {
        'products': Product.objects.all()
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

        order = Order.objects.create(
            user=request.user,
            address=address,
            total_amount=total,
            payment_method=method,
            payment_status='PAID' if method == 'ONLINE' else 'PENDING',
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


# ================= ORDERS =================

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/my_orders.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_detail.html', {'order': order})


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

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
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/invoice.html', {'order': order})


# ================= PROFILE =================

@login_required
def user_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')

        if User.objects.exclude(pk=request.user.pk).filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return redirect('store:profile')

        request.user.username = username
        request.user.email = email
        profile.phone = phone
        profile.address = address

        request.user.save()
        profile.save()

        messages.success(request, 'Profile updated successfully')
        return redirect('store:profile')

    return render(request, 'store/profile.html', {'profile': profile})


# ================= CHANGE PASSWORD =================

@login_required
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect')
            return redirect('store:change_password')

        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return redirect('store:change_password')

        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters')
            return redirect('store:change_password')

        request.user.set_password(new_password)
        request.user.save()

        messages.success(request, 'Password changed successfully. Please login again.')
        return redirect('store:login')

    return render(request, 'store/change_password.html')


# ================= NOTIFICATIONS =================

@login_required
def notifications_page(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'store/notifications.html', {'notifications': notifications})


@login_required
def delete_notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    return redirect('store:notifications')


@login_required
def clear_notifications(request):
    Notification.objects.filter(user=request.user).delete()
    return redirect('store:notifications')


# ================= STATIC PAGES =================

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
