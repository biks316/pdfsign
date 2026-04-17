from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def profile_view(request):
    return render(
        request,
        'accounts/profile.html',
        {
            'page_title': 'My Account | PDFSign Studio',
            'meta_description': 'Manage your account and connected sign-in providers.',
            'canonical_path': '/account/profile/',
        },
    )
