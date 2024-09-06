# transactions/urls.py
from django.urls import path

from .views import (
    UserTransactionListView,
    PSETransaction,
    callback,
    AccountOwnView,
    DictionariesView,
    PSETestTransaction,
)

urlpatterns = [
    path('user-transactions/<str:complex_id>/', UserTransactionListView.as_view(), name='user-transactions'),

    path('baas/pse_transaction/<str:complex_id>/<str:id>/', PSETransaction.as_view(), name='pse-transaction-get'),
    path('baas/pse_transaction/<str:complex_id>/', PSETransaction.as_view(), name='pse-transaction-post'),
    path('baas/account_own/', AccountOwnView.as_view(), name='baas-account-own'),
    path('baas/dictionaries/', DictionariesView.as_view(), name='dictionaries'),
    path('callback/', callback, name='callback'),

    path('baas/test_transaction/', PSETestTransaction.as_view(), name='pse-test-transaction'),
]