from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, null=True, blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    is_featured = models.BooleanField(default=False)  # Added to mark featured products

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.user.username

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in cart for {self.user.username}"

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError({'quantity': 'Quantity must be greater than 0.'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

    def save(self, *args, **kwargs):
        if self.pk:  # If the order already exists (update)
            old_order = Order.objects.get(pk=self.pk)
            if old_order.status != self.status:  # Status has changed
                # Create a notification
                Notification.objects.create(
                    user=self.user,
                    message=f'Order #{self.id} status updated to {self.status}.'
                )
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order {self.order.id}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"

# Signal to create UserProfile
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(
            user=instance,
            email=instance.email or '',
            phone=''
        )

# Dictionary to store the old status before saving
order_status_before_save = {}

@receiver(pre_save, sender=Order)
def store_old_status(sender, instance, **kwargs):
    try:
        old_order = Order.objects.get(id=instance.id)
        order_status_before_save[instance.id] = old_order.status
    except Order.DoesNotExist:
        # If the order doesn't exist yet (i.e., it's being created), set old status to None
        order_status_before_save[instance.id] = None

@receiver(post_save, sender=Order)
def notify_on_order_status_change(sender, instance, created, **kwargs):
    # Skip if this is a new order being created
    if created:
        return

    # Get the old status from the dictionary
    old_status = order_status_before_save.get(instance.id)
    # Clean up the dictionary
    order_status_before_save.pop(instance.id, None)

    # If the old status exists and the status has changed to 'Cancelled'
    if old_status and old_status != 'Cancelled' and instance.status == 'Cancelled':
        Notification.objects.create(
            user=instance.user,
            message=f'Your order #{instance.id} has been cancelled by an admin.'
        )