# messaging/admin.py
from django.contrib import admin

from .models import Thread, Message, ThreadStatus


class AdminMessage(admin.ModelAdmin):
    list_display = ('id', 'sender', 'type')

class AdminThreadStatus(admin.ModelAdmin):
    list_display = ('id', 'user', 'thread', 'is_deleted')


admin.site.register(Thread)
admin.site.register(Message, AdminMessage)
admin.site.register(ThreadStatus, AdminThreadStatus)