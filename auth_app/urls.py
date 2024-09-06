# auth_app/urls.py
from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from .views import (LogoutView,
                    CustomTokenObtainPairView,
                    )

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='DRF_login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
