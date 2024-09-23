# messaging/services.py
from django.db import transaction
from django.utils import timezone

from .models import Message, Thread, ThreadStatus


@transaction.atomic
def send_message(sender, recipient, subject, body, thread=None, complex=None, priority='low'):
    if not thread:
        thread = Thread.objects.create(subject=subject, complex=complex)
        thread.participants.set([sender, recipient])
        ThreadStatus.objects.create(user=sender, thread=thread, in_outbox=True, can_send=True, is_read=True, priority=priority)
        ThreadStatus.objects.create(user=recipient, thread=thread, in_inbox=True, can_send=True, priority=priority)
    else:

        thread_status = ThreadStatus.objects.get(thread=thread, user=sender)
        if not thread_status.can_send:
            return None
        thread_status.in_outbox = True
        thread_status.last_message_date = timezone.now()
        thread_status.save()

        recipients= [user for user in thread.participants.all() if user != sender] 
        for recipient in recipients:
            thread_status = ThreadStatus.objects.get(thread=thread, user=recipient)
            thread_status.is_read = False
            thread_status.is_deleted = False
            thread_status.in_inbox = True
            thread_status.last_message_date = timezone.now()
            thread_status.save()


    message = Message.objects.create(
        sender=sender,
        thread=thread,
        body=body,
        type='simple_message'
    )
    return message


@transaction.atomic
def send_massive_message(sender, subject, body, receivers, complex, priority='low'):
    
    thread= Thread.objects.create(subject=subject, complex=complex)
    thread.participants.set([sender])
    message= Message.objects.create(
        sender=sender,
        thread=thread,
        body=body,
        type='administrator_message'
    )

    ThreadStatus.objects.create(user=sender, thread=thread, can_send=True, in_outbox=True, is_read=True, priority=priority)

    for user in receivers:
        ThreadStatus.objects.create(user=user, thread=thread, can_send=False, in_inbox=True, priority=priority)

    return message
