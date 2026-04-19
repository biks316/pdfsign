from django.urls import path

from .views import checkout_view, profile_view, upgrade_view

app_name = 'accounts'

urlpatterns = [
    path('profile/', profile_view, name='profile'),
    path('upgrade/', upgrade_view, name='upgrade'),
    path('upgrade/<str:plan_slug>/', checkout_view, name='checkout'),
]
