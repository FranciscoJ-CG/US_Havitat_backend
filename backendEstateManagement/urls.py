# backendEstateManagement/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('auth_app.urls')),
    path('', include('estate_admin.urls')),
    path('messaging/', include('messaging.urls')),
    path('transactions/', include('transactions.urls')),
    path('accounting/', include('accounting.urls'))
]
