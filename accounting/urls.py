from django.urls import path

from .views import AdminFeeView

urlpatterns = [
    path('admin-fee/', AdminFeeView.as_view(), name='admin-fee'),
]