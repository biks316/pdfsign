from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render

from .models import UserPlan


@login_required
def profile_view(request):
    plan, _ = UserPlan.objects.get_or_create(user=request.user)
    return render(
        request,
        'accounts/profile.html',
        {
            'plan': plan,
            'page_title': 'My Account | PDFSign Studio',
            'meta_description': 'Manage your account and connected sign-in providers.',
            'canonical_path': '/account/profile/',
        },
    )


@login_required
def upgrade_view(request):
    plan, _ = UserPlan.objects.get_or_create(user=request.user)
    next_url = request.GET.get('next', '')
    return render(
        request,
        'accounts/upgrade.html',
        {
            'plan': plan,
            'next_url': next_url,
            'plan_prices': {
                'free': 0,
                'silver': 5,
                'gold': 10,
            },
            'page_title': 'Upgrade Plan | PDFSign Studio',
            'meta_description': 'Upgrade your plan to unlock more service attempts.',
            'canonical_path': '/account/upgrade/',
        },
    )


@login_required
def checkout_view(request, plan_slug: str):
    plan_slug = (plan_slug or '').lower()
    if plan_slug not in {UserPlan.PLAN_SILVER, UserPlan.PLAN_GOLD}:
        return redirect('accounts:upgrade')

    plan, _ = UserPlan.objects.get_or_create(user=request.user)
    amount = 5 if plan_slug == UserPlan.PLAN_SILVER else 10

    if request.method == 'POST':
        plan.plan = plan_slug
        plan.save(update_fields=['plan', 'updated_at'])
        messages.success(request, f'Payment successful. Your plan is now {plan.get_plan_display()} (${amount}/month).')
        return redirect('accounts:profile')

    return render(
        request,
        'accounts/checkout.html',
        {
            'target_plan': plan_slug,
            'amount': amount,
            'current_plan': plan,
            'page_title': 'Checkout | PDFSign Studio',
            'meta_description': 'Secure checkout to upgrade your plan.',
            'canonical_path': f'/account/upgrade/{plan_slug}/',
        },
    )


@staff_member_required(login_url='account_login')
def admin_latest_users_view(request):
    User = get_user_model()
    users = (
        User.objects
        .order_by('-date_joined')
        .prefetch_related('socialaccount_set')[:200]
    )
    return render(
        request,
        'accounts/admin_users.html',
        {
            'users': users,
            'page_title': 'Admin Users | PDFSign Studio',
            'meta_description': 'Latest registered users and linked social providers.',
            'canonical_path': '/admin/',
        },
    )
