from django.urls import path
from .views import DocumentsView, DocumentDownloadView 

urlpatterns = [
    path('<str:complex_id>/', DocumentsView.as_view(), name='documents'),
    path('document/<int:pk>/', DocumentDownloadView.as_view(), name='document-download'),

]
