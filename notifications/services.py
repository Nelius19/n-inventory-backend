from .models import Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def check_low_stock_notification(user, item):
    # if item quantity is more than minimum limit, return        
    if(item.quantity > item.min_limit):
        return

    # quantity is less than minimum limit
    notification = Notification.objects.create(
        user=user, 
        title="Low Stock Alert",
        item_name=item.name,
        quantity=item.quantity,
        type="low_stock",
    )

    # retrieve channel layer to broadcast messages outside of consumers
    channel_layer = get_channel_layer()

    # send notification event to all WebSocket clients in the user's group
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}",
        {
            "type": "send_notification",
            "notification": {
                "title": notification.title,
                "item_name": notification.item_name,
                "quantity": notification.quantity,
                "type": notification.type,
            }
        }
    )

    return notification
