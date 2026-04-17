from django.urls import path

from .views import (
    add_date_editor_view,
    add_date_view,
    pdf_tools_index_view,
    sign_pdf_editor_view,
    sign_pdf_view,
)

app_name = 'pdf_tools'

urlpatterns = [
    path('', pdf_tools_index_view, name='index'),
    path('sign-pdf/', sign_pdf_view, name='sign_pdf'),
    path('sign-pdf/editor/<str:file_id>/', sign_pdf_editor_view, name='sign_pdf_editor'),
    path('add-date-to-pdf/', add_date_view, name='add_date'),
    path('add-date-to-pdf/editor/<str:file_id>/', add_date_editor_view, name='add_date_editor'),
]
