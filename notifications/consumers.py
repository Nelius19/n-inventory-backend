from channels.generic.websocket import AsyncWebsocketConsumer
import json

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']

        # close connect is user is not authenticated
        if not user.is_authenticated:
            await self.close()
            return
        
        # add current channel to the user's group
        await self.channel_layer.group_add(
            f"user_{user.id}",
            self.channel_name
        )

        # accept connection
        await self.accept()

    # recieves event payload from services.py
    async def send_notification(self, event):
        # Await sending the response back to client side
        await self.send(text_data=json.dumps({
            "notification": event["notification"]
        }))
