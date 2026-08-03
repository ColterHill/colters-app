from django.urls import path
from . import views

app_name = 'po_processing'

urlpatterns = [
    path('upload-po/', views.POUploadView.as_view(), name='upload_po'),
    path('suppliers/', views.get_suppliers, name='get_suppliers'),
    path('upload-status/<uuid:upload_id>/', views.get_upload_status, name='get_upload_status'),
    path('upload-history/', views.get_upload_history, name='get_upload_history'),
]
