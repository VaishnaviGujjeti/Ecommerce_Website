from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages 
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Category, Product, CartItem, UserProfile, Order, OrderItem, Notification
from django.core.paginator import Paginator
from .forms import RegisterForm, CustomUserCreationForm, ProfileForm
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.messages import get_messages
from datetime import datetime
import pytz

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # This triggers the signal to create a UserProfile
            # Update the existing UserProfile instead of creating a new one
            user_profile = user.userprofile
            user_profile.email = form.cleaned_data['email']
            user_profile.phone = ''
            user_profile.save()
            login(request, user)
            messages.success(request, 'Signup successful!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'shop/signup.html', {'form': form, 'show_footer': False})

class RegisterForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=False)

    class Meta:
        model = UserProfile
        fields = ['email', 'phone']

    def save(self, commit=True):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        email = self.cleaned_data['email']
        user = User.objects.create_user(username=username, password=password, email=email)
        user_profile = super().save(commit=False)
        user_profile.user = user
        if commit:
            user_profile.save()
        return user_profile

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user_profile = form.save()
            user = user_profile.user
            login(request, user)
            messages.success(request, 'Registration successful! Welcome!')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'shop/register.html', {'form': form, 'show_footer': False})

def login_view(request):
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%I:%M %p IST, %A, %B %d, %Y')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}!')
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'shop/login.html', {'form': form, 'current_time': current_time, 'show_footer': False})

def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('home')

def home(request):
    featured_products = Product.objects.filter(is_featured=True)[:3]
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    else:
        notifications = []
    return render(request, 'shop/home.html', {
        'notifications': notifications,
        'featured_products': featured_products,
        'show_footer': True
    })

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        messages.success(request, f'Thank you, {name}! Your message has been received.')
        return redirect('contact')
    return render(request, 'shop/contact.html', {'show_footer': True})

def products(request):
    category_slug = request.GET.get('category')
    sort_by = request.GET.get('sort_by', 'name')
    search_query = request.GET.get('search', '').strip()
    products = Product.objects.all()

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    else:
        products = products.order_by('name')

    paginator = Paginator(products, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()
    return render(request, 'shop/products.html', {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_slug,
        'sort_by': sort_by,
        'search_query': search_query,
        'show_footer': True
    })

def product_list(request):
    products = Product.objects.all().order_by('name')
    paginator = Paginator(products, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'shop/product_list.html', {
        'page_obj': page_obj,
        'show_footer': True
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'shop/product_detail.html', {
        'product': product,
        'show_footer': True
    })

@login_required
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login') 
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, f'{product.name} added to cart!')
    if 'product' in request.path and 'add-to-cart' not in request.path:
        return redirect('product_detail', product_id=product_id)
    return redirect('cart')

@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f'{product_name} has been removed from your cart.')
    return redirect('cart')

@login_required
def increase_quantity(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)
    cart_item.quantity += 1
    cart_item.save()
    messages.success(request, f'Quantity of {cart_item.product.name} increased to {cart_item.quantity}.')
    return redirect('cart')

@login_required
def decrease_quantity(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
        messages.success(request, f'Quantity of {cart_item.product.name} decreased to {cart_item.quantity}.')
    else:
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f'{product_name} has been removed from your cart.')
    return redirect('cart')

@login_required
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'shop/cart.html', {'cart_items': cart_items, 'total': total, 'show_footer': True})

@login_required
def checkout(request):
    if request.method == 'POST':
        selected_item_ids = request.POST.getlist('selected_items')
        
        if not selected_item_ids:
            messages.error(request, 'Please select at least one item to checkout.')
            return redirect('cart')

        cart_items = CartItem.objects.filter(user=request.user, id__in=selected_item_ids).select_related('product')
        print(f"Selected Cart Items Count: {cart_items.count()}")

        cart_items_list = list(cart_items)
        for cart_item in cart_items_list:
            try:
                if not cart_item.product or not cart_item.product.name or cart_item.product.price <= 0:
                    messages.error(request, f'Invalid product in cart: {cart_item.product}')
                    return redirect('cart')
                print(f"Cart Item: {cart_item.product.name} (x{cart_item.quantity})")
            except ObjectDoesNotExist:
                messages.error(request, f'Product {cart_item.product_id} no longer exists.')
                return redirect('cart')

        total = sum(item.product.price * item.quantity for item in cart_items_list)
        print(f"Total: {total}")

        if total <= 0:
            messages.error(request, 'Cart total is invalid.')
            return redirect('cart')

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                total_amount=total,
                status='Pending'
            )
            print(f"Created Order: {order}")

            order_items_created = 0
            for cart_item in cart_items_list:
                try:
                    order_item = OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.price
                    )
                    order_items_created += 1
                    print(f"Created OrderItem: {order_item}")
                except Exception as e:
                    print(f"Failed to create OrderItem: {e}")
                    raise

            if order_items_created == 0 or not order.order_items.exists():
                order.delete()
                raise ValueError("Failed to create any OrderItems for the order.")

            Notification.objects.create(
                user=request.user,
                message=f'Your order #{order.id} has been placed successfully.'
            )

            cart_items.delete()

        return redirect('order_confirmation', order_id=order.id)
    
    return redirect('cart')

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('order_items__product'), id=order_id, user=request.user)
    print(f"Order Confirmation for Order {order.id}:")
    items = order.order_items.all()
    print(f"  Number of Items: {items.count()}")
    for item in items:
        print(f"    Item: {item.product.name} (x{item.quantity}) - ${item.price}")
    
    latest_notification = Notification.objects.filter(user=request.user).order_by('-created_at').first()
    
    storage = get_messages(request)
    for message in storage:
        pass
    storage.used = True
    
    return render(request, 'shop/order_confirmation.html', {
        'order': order,
        'latest_notification': latest_notification,
        'show_footer': True
    })

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at').prefetch_related('order_items__product')
    paginator = Paginator(orders, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    for order in page_obj:
        print(f"Order {order.id} (Status: {order.status}):")
        items = order.order_items.all()
        print(f"  Number of Items: {items.count()}")
        for item in items:
            print(f"    Item: {item.product.name} (x{item.quantity}) - ${item.price}")
    return render(request, 'shop/order_history.html', {'page_obj': page_obj, 'show_footer': False})

@login_required
def notifications(request):
    user_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(user_notifications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'shop/notifications.html', {'page_obj': page_obj, 'show_footer': False})

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    messages.success(request, 'Notification marked as read.')
    return redirect('notifications')

@login_required
def profile(request):
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(
            user=request.user,
            email=request.user.email or '',
            phone=''
        )
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=user_profile)
    return render(request, 'shop/profile.html', {'form': form, 'show_footer': True})