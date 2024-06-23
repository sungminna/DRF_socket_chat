from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message, ShopUser, VisitorUser


class ChatConsumer(AsyncJsonWebsocketConsumer):
    # inherited to serialize or deserialize json and python object
    async def connect(self):  # make conn
        try:
            # extract id
            self.room_id = self.scope['url_route']['kwargs']['room_id']
            if not await self.check_room_exists(self.room_id):
                raise ValueError('Room does not exist')
            group_name = self.get_group_name(self.room_id)
            # add channel to group
            await self.channel_layer.group_add(group_name, self.channel_name)
            await self.accept()
        except ValueError as e:
            await self.send_json({'error': str(e)})
            await self.close()

    async def disconnect(self, close_code):  # disconnect
        try:
            group_name = self.get_group_name(self.room_id)
            # delete channel form group
            await self.channel_layer.group_discard(group_name, self.channel_name)
        except Exception as e:
            pass

    async def receive_json(self, content):  # triggered when client sends json
        try:
            # extract data from json
            message = content['message']
            sender_email = content['sender_email']
            shop_user_email = content.get('shop_user_email')
            visitor_user_email = content.get('visitor_user_email')
            if not shop_user_email or not visitor_user_email:
                raise ValueError("User and visitor email are required")

            # make room or get existing room
            room = await self.get_or_create_room(shop_user_email, visitor_user_email)
            self.room_id = str(room.id)
            group_name = self.get_group_name(self.room_id)
            # save to db
            await self.save_message(room, sender_email, message)
            # send message to entire group
            await self.channel_layer.group_send(group_name, {
                'type': 'chat_message',
                'message': message,
                'sender_email': sender_email,
            })
        except ValueError as e:
            await self.send_json({'error': str(e)})

    async def chat_message(self, event):  # braodcast messages to all channels on group
        try:
            # extract date from json
            message = event['message']
            sender_email = event['sender_email']

            await self.send_json({'message': message, 'sender_email': sender_email})
        except Exception as e:
            await self.send_json({'error': str('failed to send message')})

    @staticmethod
    def get_group_name(room_id):
        return f'chat_room_{room_id}'

    @database_sync_to_async  # use sync(db) code in asyc(ws) code without poor performance
    def get_or_create_room(self, shop_user_email, visitor_user_email):
        shop_user, _ = ShopUser.objects.get_or_create(shop_user_email=shop_user_email)
        visitor_user, _ = VisitorUser.objects.get_or_create(visitor_user_email=visitor_user_email)

        room, created = ChatRoom.objects.get_or_create(
            shop_user=shop_user,
            visitor_user=visitor_user,
        )
        return room

    @database_sync_to_async
    def save_message(self, room, sender_email, message_text):
        if not sender_email or not message_text:
            raise ValueError("User and message text are required")
        Message.objects.create(room=room, sender_email=sender_email, text=message_text)

    @database_sync_to_async
    def check_room_exists(self, room_id):
        return ChatRoom.objects.filter(id=room_id).exists()
