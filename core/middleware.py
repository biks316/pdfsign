import os
from urllib.parse import urlencode

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class ServiceLoginRequiredMiddleware:
    """Require authentication for all tool service routes."""

    PROTECTED_PREFIXES = (
        '/pdf-tools/',
        '/image-tools/',
        '/signer/',
        '/sign/',
    )
    OAUTH_PROVIDER_ENV_KEYS = {
        '/accounts/google/login/': ('GOOGLE_OAUTH_CLIENT_ID', 'GOOGLE_OAUTH_SECRET'),
        '/accounts/microsoft/login/': ('MICROSOFT_OAUTH_CLIENT_ID', 'MICROSOFT_OAUTH_SECRET'),
        '/accounts/github/login/': ('GITHUB_OAUTH_CLIENT_ID', 'GITHUB_OAUTH_SECRET'),
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        is_protected = self._is_protected(path)
        should_count_attempt = is_protected and request.user.is_authenticated and request.method == 'POST'
        oauth_redirect = self._maybe_redirect_unconfigured_oauth(request, path)
        if oauth_redirect is not None:
            return oauth_redirect
        if is_protected and not request.user.is_authenticated:
            login_url = reverse('account_login')
            query = urlencode({'next': request.get_full_path()})
            return redirect(f'{login_url}?{query}')

        if is_protected and request.user.is_authenticated:
            plan = self._get_user_plan(request.user)
            if not plan.can_attempt():
                messages.error(
                    request,
                    f'Plan limit reached: {plan.max_attempts} attempts used. Upgrade plan to continue.',
                    fail_silently=True,
                )
                return redirect(f"{reverse('accounts:upgrade')}?next={request.get_full_path()}")

        response = self.get_response(request)
        if should_count_attempt and response.status_code < 400:
            plan = self._get_user_plan(request.user)
            plan.register_attempt()
        return response

    @classmethod
    def _is_protected(cls, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in cls.PROTECTED_PREFIXES)

    @classmethod
    def _missing_oauth_config(cls, path: str) -> bool:
        required_keys = cls.OAUTH_PROVIDER_ENV_KEYS.get(path)
        if not required_keys:
            return False
        return any(not os.getenv(key) for key in required_keys)

    def _maybe_redirect_unconfigured_oauth(self, request, path: str):
        if path not in self.OAUTH_PROVIDER_ENV_KEYS:
            return None
        if not self._missing_oauth_config(path):
            return None
        messages.error(
            request,
            'OAuth provider is not configured yet. Add client ID/secret in .env and restart.',
            fail_silently=True,
        )
        return redirect(reverse('account_signup'))

    @staticmethod
    def _get_user_plan(user):
        from accounts.models import UserPlan

        plan, _ = UserPlan.objects.get_or_create(user=user)
        return plan
