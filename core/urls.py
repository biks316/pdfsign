from django.urls import path

from .views import home_view, robots_txt_view

app_name = 'core'

urlpatterns = [
    path('', home_view, name='home'),
    path('robots.txt', robots_txt_view, name='robots_txt'),
]
