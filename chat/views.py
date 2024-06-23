from http.client import HTTPException

from django.shortcuts import render
from rest_framework import generics, serializers, status
from rest_framework.response import Response
from .models import ChatRoom, Message, ShopUser, VisitorUser
from .serializers import ChatRoomSerializer, MessageSerializer
from rest_framework.exceptions import ValidationError
from django.http import Http404
from django.http import JsonResponse
from django.conf import settings

# Create your views here.

class ImmediateResponseException(Exception):  # send immediate http when exception occurs
    def __init__(self, response):
        self.response = response

# get chatroom list
class ChatRoomListCreateView(generics.ListCreateAPIView):
    # assign serializer to use
    serializer_class = ChatRoomSerializer

    # GET request queryset
    def get_queryset(self):
        try:
            # get email from query params or None
            user_email = self.request.query_params.get('email', None)
            if not user_email:
                raise ValidationError('user_email is required')
            # find chatroom that user_email is in
            return ChatRoom.objects.filter(
                shop_user__shop_user_email=user_email
            ) | ChatRoom.objects.filter(
                visitor_user__visitor_user_email=user_email
            )
        except ValidationError as e:
            content = {'detail': e.detail}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            content = {'detail': str(e)}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

    # config serializer context
    def get_serializer_context(self):
        # get context
        context = super(ChatRoomListCreateView, self).get_serializer_context()
        # add request to context
        context['request'] = self.request
        return context

    # POST request queryset
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            # save data using serializer
            self.perform_create(serializer)
        except ImmediateResponseException as e:
            return e.response
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    # save object to db using serializer
    def perform_create(self, serializer):
        # get info from request
        shop_user_email = self.request.data.get('shop_user_email')
        visitor_user_email = self.request.data.get('visitor_user_email')
        # get object or make one
        shop_user, _ = ShopUser.objects.get_or_create(shop_user_email=shop_user_email)
        visitor_user, _ = VisitorUser.objects.get_or_create(visitor_user_email=visitor_user_email)
        # find same chatroom existence
        existing_chatroom = ChatRoom.objects.filter(shop_user__shop_user_email=shop_user_email, visitor_user__visitor_user_email=visitor_user_email).first()
        if existing_chatroom:
            serializer = ChatRoomSerializer(existing_chatroom, context={'request': self.request})
            print(serializer.data)
            raise ImmediateResponseException(Response(serializer.data, status=status.HTTP_200_OK))
        # save to db
        serializer.save(shop_user=shop_user, visitor_user=visitor_user)

# get message list
class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer

    # GET request queryset
    def get_queryset(self):
        room_id = self.kwargs.get('room_id')
        if not room_id:
            content = {'detail': 'room_id is required'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        queryset = Message.objects.filter(room_id=room_id)
        if not queryset.exists():
            raise Http404('room_id is invalid')

        return queryset


