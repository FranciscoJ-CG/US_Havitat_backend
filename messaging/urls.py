# messaging/urls.py
from django.urls import path

from .views import ( 
                    message_box_view,
                    delete_threads_view,
                    thread_view,
                    send_message_view,
                    send_massive_message_view,
                    )

urlpatterns = [
    path('message_box/<int:complex_id>', message_box_view, name='message_box_view'),
    path('thread/<int:thread_id>/', thread_view, name='thread_view'),
    path('delete_threads/', delete_threads_view, name='delete_threads_view'),
    path('send_message/', send_message_view, name='send_message_view'),
    path('send_massive_message/', send_massive_message_view, name='send_massive_message'),
]
