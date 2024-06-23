from django.db import models

# Create your models here.

# 1:1 chatting
class ShopUser(models.Model):
    shop_user_email = models.EmailField(unique=True)

class VisitorUser(models.Model):
    visitor_user_email = models.EmailField(unique=True)

class ChatRoom(models.Model):
    shop_user = models.ForeignKey(ShopUser, on_delete=models.CASCADE)
    visitor_user = models.ForeignKey(VisitorUser, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('shop_user', 'visitor_user')


class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender_email = models.EmailField()
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
