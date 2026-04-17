from django.urls import path

from . import views

app_name = 'signer'

urlpatterns = [
    path('', views.upload_pdf_view, name='upload'),
    path('sign/<str:file_id>/', views.sign_pdf_view, name='sign'),
]
