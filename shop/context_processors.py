from datetime import datetime
import pytz
from .models import CartItem, Notification

def current_time(request):
    ist = pytz.timezone('Asia/Kolkata')
    return {'current_time': datetime.now(ist).strftime('%I:%M %p IST, %A, %B %d, %Y')}


def navbar_counts(request):
    if not request.user.is_authenticated:
        return {
            'cart_items_count': 0,
            'unread_notifications_count': 0,
        }
    
    # Calculate cart items count (sum of quantities)
    cart_items = CartItem.objects.filter(user=request.user)
    cart_items_count = sum(item.quantity for item in cart_items)
    
    # Calculate unread notifications count
    unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return {
        'cart_items_count': cart_items_count,
        'unread_notifications_count': unread_notifications_count,
    }