from django.contrib import admin

from .models import Transaction, TransactionLog, AccountInfo

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'transfer_id', 'amount',  'status')

class AccountInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'complex', 'account_number')

admin.site.register(AccountInfo, AccountInfoAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(TransactionLog)
