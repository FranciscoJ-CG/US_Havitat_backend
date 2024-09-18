# messaging/models.py
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Thread(models.Model):
    subject = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL)
    complex = models.ForeignKey('estate_admin.Complex', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return str(self.id) + " - " + self.subject
        

class ThreadStatus(models.Model):
    last_message_date = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    can_send= models.BooleanField(default=False)
    in_inbox= models.BooleanField(default=False)
    in_outbox= models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    tags = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Thread: {self.thread.subject}, User: {self.user}"

    class Meta:
        unique_together = ('user', 'thread')
        indexes = [
            models.Index(fields=['last_message_date']),
            models.Index(fields=['user', 'thread']),
        ]


class Message(models.Model):
    class MessageType(models.TextChoices):
        ADMINISTRATOR_MESSAGE = 'administrator_message', 'Administrator Message'
        SIMPLE_MESSAGE = 'simple_message', 'Simple Message'
        SYSTEM_NOTIFICATION = 'system_notification', 'System Notification'

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=21, choices=MessageType.choices)

    def __str__(self):
        return f"{self.sender} to {self.thread.subject} - {self.type}"
    
    def save(self, *args, **kwargs):
        if not len(self.body.strip()) > 1:
            raise ValidationError("The message cannot be empty")
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['thread', 'type']),
        ]