from django.urls import path

from .views import (
    about_view,
    contact_view,
    faq_view,
    how_it_works_view,
    privacy_view,
    terms_view,
)

app_name = 'pages'

urlpatterns = [
    path('about/', about_view, name='about'),
    path('faq/', faq_view, name='faq'),
    path('privacy/', privacy_view, name='privacy'),
    path('terms/', terms_view, name='terms'),
    path('contact/', contact_view, name='contact'),
    path('how-it-works/', how_it_works_view, name='how_it_works'),
]
