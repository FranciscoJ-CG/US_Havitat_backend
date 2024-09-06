from django.contrib import admin

from .models import (AdminFee,)


class AdminFeeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'timestamp',  'unit', 'state', 'expiration_date', 'transaction', 'amount')  

admin.site.register(AdminFee, AdminFeeAdmin)