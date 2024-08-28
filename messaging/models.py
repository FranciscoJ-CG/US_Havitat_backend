# messaging/models.py
from django.conf import settings
from django.db import models
from django.utils import timezone


class Thread(models.Model):
    subject = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL)
    # complexes = models.ManyToManyField('estate_admin.Complex', blank=True)
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
        return f"Status of {self.thread.subject} for {self.user}"


class Message(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('administrator_message', 'Administrator Message'),
        ('simple_message', 'Simple Message'),
        ('system_notification', 'System Notification')
    ]
    
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=21, choices=MESSAGE_TYPE_CHOICES)

    def __str__(self):
        return f"{self.sender} to {self.thread.subject} - {self.type}"