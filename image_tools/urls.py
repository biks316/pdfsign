from django.urls import path

from .views import (
    compress_image_view,
    convert_image_view,
    crop_image_view,
    enhance_document_view,
    image_to_pdf_view,
    index_view,
    remove_background_view,
    resize_image_view,
)

app_name = 'image_tools'

urlpatterns = [
    path('', index_view, name='index'),
    path('image-to-pdf/', image_to_pdf_view, name='image_to_pdf'),
    path('resize-image/', resize_image_view, name='resize_image'),
    path('compress-image/', compress_image_view, name='compress_image'),
    path('crop-image/', crop_image_view, name='crop_image'),
    path('convert-image/', convert_image_view, name='convert_image'),
    path('remove-background/', remove_background_view, name='remove_background'),
    path('enhance-document/', enhance_document_view, name='enhance_document'),
]
