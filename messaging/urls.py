# messaging/urls.py
from django.urls import path

from .views import inbox_view, outbox_view, delete_threads_view, thread_view, send_message_view, send_massive_message_view

urlpatterns = [
    path('inbox/<int:complex_id>/', inbox_view, name='inbox_view'),
    path('outbox/<int:complex_id>/', outbox_view, name='outbox_view'),
    path('thread/<int:thread_id>/', thread_view, name='thread_view'),
    path('delete_threads/', delete_threads_view, name='delete_threads_view'),
    path('send_message/', send_message_view, name='send_message_view'),
    path('send_massive_message/', send_massive_message_view, name='send_massive_message'),
]
