from django.conf import settings


def seo_defaults(request):
    return {
        'SITE_NAME': settings.SITE_NAME,
        'SITE_DOMAIN': settings.SITE_DOMAIN,
        'DEFAULT_OG_IMAGE': f"{settings.SITE_DOMAIN}/static/img/og-default.svg",
    }
