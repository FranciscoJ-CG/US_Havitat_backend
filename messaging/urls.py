# messaging/urls.py
from django.urls import path

from .views import ( 
                    message_box_view,
                    thread_view,
                    send_message_view,
                    send_notifications_view,
                    )

urlpatterns = [
    path('message_box/<int:complex_id>/<str:view>', message_box_view, name='message_box_view'),
    path('thread/', thread_view, name='delete_thread_view'),
    path('thread/<int:thread_id>/', thread_view, name='thread_view'),
    path('send_message/', send_message_view, name='send_message_view'),
    path('send_notifications/', send_notifications_view, name='send_notifications'),
]
