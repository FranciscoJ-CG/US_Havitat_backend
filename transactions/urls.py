# transactions/urls.py
from django.urls import path

from .views import (
    UserTransactionListView,
    PSETransaction,
    callback,
    AccountOwnView,
    DictionariesView,
    AccountHistoryView, 
    PSETestTransaction,
)

urlpatterns = [
    path('user-transactions/', UserTransactionListView.as_view(), name='user-transactions'),

    path('baas/pse_transaction/<str:id>/', PSETransaction.as_view(), name='pse-transaction'),
    path('baas/account_own/', AccountOwnView.as_view(), name='baas-account-own'),
    path('baas/dictionaries/', DictionariesView.as_view(), name='dictionaries'),
    path('baas/account_history/', AccountHistoryView.as_view(), name='baas-account-history'),
    path('callback/', callback, name='callback'),

    path('baas/test_transaction/', PSETestTransaction.as_view(), name='pse-test-transaction'),
]