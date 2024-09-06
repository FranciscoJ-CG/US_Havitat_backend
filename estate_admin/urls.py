# estate_admin/urls.py

from django.urls import path
from .views import (
                    UnitDetail,
                    ComplexManagement,
                    UnitManagement,
                    ComplexInfoView,
)

urlpatterns = [
    path('complex_info/<str:complex_id>/', ComplexInfoView.as_view(), name='complex-info'),
    path('unit/<int:id>/', UnitDetail.as_view(), name='unit_detail'),
    path('admin-home/', ComplexManagement.as_view(), name='admin_home'),
    path('client-home/', UnitManagement.as_view(), name='client_home'),
]