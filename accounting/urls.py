from django.urls import path

from .views import AdminFeeListView, AdminFeeView

urlpatterns = [
    path('admin-fee/', AdminFeeView.as_view(), name='admin-fee'),
    path('fees/', AdminFeeListView.as_view(), name='admin_fee_list'),
]