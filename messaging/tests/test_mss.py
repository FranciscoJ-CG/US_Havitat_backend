import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from messaging.models import Thread, ThreadStatus, Message
from auth_app.models import User

import time

@pytest.fixture
def user1():
    return User.objects.create(username="user1")

@pytest.fixture
def user2():
    return User.objects.create(username="user2")

@pytest.fixture
def thread(user1, user2):
    thread = Thread.objects.create(subject="Test Thread")
    thread.participants.add(user1, user2)
    return thread

@pytest.fixture
def thread_status(user1, thread):
    return ThreadStatus.objects.create(user=user1, thread=thread)

@pytest.fixture
def message(user1, thread):
    return Message.objects.create(
        sender=user1,
        thread=thread,
        body="Test message",
        type="simple_message"
    )


@pytest.mark.django_db
class TestThread:
    def test_create_thread(self, thread, user1, user2):
        assert thread.subject == "Test Thread"
        assert thread.created_at is not None
        assert list(thread.participants.all()) == [user1, user2]

    def test_str_representation(self, thread):
        assert str(thread) == f"{thread.id} - Test Thread"

    @pytest.mark.parametrize("subject", [
        "",
        "A" * 256,  # Exceeds max_length
    ])
    def test_invalid_subject(self, subject):
        with pytest.raises(ValidationError):
            Thread.objects.create(subject=subject).full_clean()

    def test_null_subject(self):
        with pytest.raises(IntegrityError):
            Thread.objects.create(subject=None)


@pytest.mark.django_db
class TestThreadStatus:
    def test_create_thread_status(self, thread_status, user1, thread):
        assert thread_status.user == user1
        assert thread_status.thread == thread
        assert thread_status.can_send is False
        assert thread_status.in_inbox is False
        assert thread_status.in_outbox is False
        assert thread_status.is_read is False
        assert thread_status.is_deleted is False
        assert thread_status.tags is None

    def test_str_representation(self, thread_status, user1):
        
        assert str(thread_status) ==f"Thread: {thread_status.thread.subject}, User: {str(user1)}"

    @pytest.mark.parametrize("field,value", [
        ("can_send", True),
        ("in_inbox", True),
        ("in_outbox", True),
        ("is_read", True),
        ("is_deleted", True),
        ("tags", "important,urgent"),
    ])
    def test_update_thread_status(self, thread_status, field, value):
        setattr(thread_status, field, value)
        thread_status.save()
        thread_status.refresh_from_db()
        assert getattr(thread_status, field) == value

    def test_tags_max_length(self, thread_status):
        with pytest.raises(ValidationError):
            thread_status.tags = "A" * 256
            thread_status.full_clean()

@pytest.mark.django_db
class TestMessage:
    def test_create_message(self, message, user1, thread):
        assert message.sender == user1
        assert message.thread == thread
        assert message.body == "Test message"
        assert message.created_at is not None
        assert message.type == "simple_message"

    def test_str_representation(self, message):
        assert str(message) == f"{message.sender} to Test Thread - simple_message"

    @pytest.mark.parametrize("message_type", [
        "administrator_message",
        "simple_message",
        "system_notification",
    ])
    def test_valid_message_types(self, user1, thread, message_type):
        message = Message.objects.create(
            sender=user1,
            thread=thread,
            body="Test message",
            type=message_type
        )
        message.full_clean()

    def test_message_without_type(self, user1, thread):
        with pytest.raises(ValidationError):
            Message.objects.create(
                sender=user1,
                thread=thread,
                body="Test message",
            ).full_clean()

    def test_message_without_body(self, user1, thread):
        with pytest.raises(ValidationError):
            Message.objects.create(
                sender=user1,
                thread=thread,
                body="",
                type="simple_message"
            ).full_clean()

@pytest.mark.django_db
class TestRelationships:
    def test_thread_participants(self, thread, user1, user2):
        assert list(thread.participants.all()) == [user1, user2]

    def test_user_threads(self, thread, user1):
        assert list(user1.thread_set.all()) == [thread]

    def test_thread_messages(self, thread, message):
        assert list(thread.message_set.all()) == [message]

    def test_user_sent_messages(self, user1, message):
        assert list(user1.sent_messages.all()) == [message]

    def test_thread_status_cascade_delete(self, thread_status, thread):
        thread.delete()
        with pytest.raises(ThreadStatus.DoesNotExist):
            thread_status.refresh_from_db()

    def test_message_cascade_delete(self, message, thread):
        thread.delete()
        with pytest.raises(Message.DoesNotExist):
            message.refresh_from_db()


@pytest.mark.django_db
class TestEdgeCases:
    def test_thread_without_participants(self):
        thread = Thread.objects.create(subject="Empty Thread")
        assert thread.participants.count() == 0

    def test_thread_with_many_participants(self, user1):
        thread = Thread.objects.create(subject="Many Participants")
        users = [User.objects.create(username=f"user{i}") for i in range(2, 101)]  # Start from 2 to avoid conflict with user1
        thread.participants.add(user1, *users)
        assert thread.participants.count() == 100

    def test_long_message_body(self, user1, thread):
        long_body = "A" * 10000  # Very long message body
        message = Message.objects.create(
            sender=user1,
            thread=thread,
            body=long_body,
            type="simple_message"
        )
        assert message.body == long_body

    def test_multiple_thread_statuses_per_user(self, user1):
        threads = [Thread.objects.create(subject=f"Thread {i}") for i in range(5)]
        for thread in threads:
            ThreadStatus.objects.create(user=user1, thread=thread)
        assert ThreadStatus.objects.filter(user=user1).count() == 5

    def test_message_created_at_ordering(self, user1, thread):
        messages = [
            Message.objects.create(
                sender=user1,
                thread=thread,
                body=f"Message {i}",
                type="simple_message"
            )
            for i in range(5)
        ]
        assert list(thread.message_set.order_by('created_at')) == messages