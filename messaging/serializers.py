# messaging/serializers.py
from rest_framework import serializers
from .models import Thread, ThreadStatus, Message
from auth_app.models import User



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class ThreadSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Thread
        fields = ['id', 'subject', 'participants', 'complex']


class ThreadStatusSerializer(serializers.ModelSerializer):
    thread = ThreadSerializer(read_only=True)

    class Meta:
        model = ThreadStatus
        fields = ['id', 'user', 'thread', 'can_send', 'is_read', 'is_deleted', 'in_inbox', 'in_outbox', 'last_message_date']



class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
 
    class Meta:
        model = Message
        fields = ['id', 'sender', 'thread', 'body', 'created_at', 'type']


class MassiveMessageInputSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=255)
    body = serializers.CharField()
    complex_id = serializers.IntegerField()
