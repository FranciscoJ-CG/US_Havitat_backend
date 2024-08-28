# estate_admin/urls.py

from django.urls import path
from .views import (
                    ComplexUnits,
                    UnitDetail,
                    get_managed_complexes,
                    get_related_units,
)

urlpatterns = [
    path('unit/<int:id>/', UnitDetail.as_view(), name='unit_detail'),
    path('unit-list/<int:complex_id>/', ComplexUnits.as_view(), name='complex_units'),
    
    path('admin-home/', get_managed_complexes, name='admin_home'),
    path('client-home/', get_related_units, name='client_home'),
]