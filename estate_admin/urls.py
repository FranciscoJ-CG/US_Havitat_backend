# estate_admin/urls.py

from django.urls import path
from .views import (
                    ComplexUnits,
                    UnitDetail,
                    ComplexManagement,
                    UnitManagement
)

urlpatterns = [
    path('unit/<int:id>/', UnitDetail.as_view(), name='unit_detail'),
    path('unit-list/<int:complex_id>/', ComplexUnits.as_view(), name='complex_units'),
    path('admin-home/', ComplexManagement.as_view(), name='admin_home'),
    path('client-home/', UnitManagement.as_view(), name='client_home'),
]