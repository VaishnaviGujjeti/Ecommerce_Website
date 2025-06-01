from django.contrib import admin
from .models import Category, Product, CartItem, UserProfile, Order, OrderItem, Notification

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}  # Auto-fill slug based on name

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_featured']
    list_filter = ['category', 'is_featured']
    search_fields = ['name', 'description']
    list_editable = ['is_featured']  # Allow editing is_featured directly in the list view

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity']
    list_filter = ['user']
    search_fields = ['user__username', 'product__name']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'email', 'phone']
    search_fields = ['user__username', 'email']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'status', 'created_at', 'has_items']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username']
    inlines = [OrderItemInline]

    def has_items(self, obj):
        return obj.order_items.exists()
    has_items.boolean = True
    has_items.short_description = 'Has Items'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price']
    list_filter = ['order']
    search_fields = ['order__id', 'product__name']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['user__username', 'message']