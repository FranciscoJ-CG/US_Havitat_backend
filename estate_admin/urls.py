# estate_admin/urls.py

from django.urls import path
from .views import (
                    UnitDetail,
                    UnitManagement,
                    ComplexInfoView,
                    ComplexImageView,
)

urlpatterns = [
    path('complex_info/<str:complex_id>/', ComplexInfoView.as_view(), name='complex-info'),
    path('unit/<int:id>/', UnitDetail.as_view(), name='unit_detail'),
    path('client-home/', UnitManagement.as_view(), name='client_home'),
    path('complex_image/<int:complex_id>/', ComplexImageView.as_view(), name='complex_image_detail'),
]