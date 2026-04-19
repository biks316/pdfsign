from django import forms

from .models import UserPlan


class PlanSignupForm(forms.Form):
    plan = forms.ChoiceField(
        choices=UserPlan.PLAN_CHOICES,
        initial=UserPlan.PLAN_FREE,
        widget=forms.HiddenInput(),
    )

    def clean_plan(self):
        value = self.cleaned_data.get('plan') or UserPlan.PLAN_FREE
        valid_values = {choice[0] for choice in UserPlan.PLAN_CHOICES}
        if value not in valid_values:
            return UserPlan.PLAN_FREE
        return value

    def signup(self, request, user):
        plan_obj, _ = UserPlan.objects.get_or_create(user=user)
        plan_obj.plan = self.cleaned_data['plan']
        plan_obj.save(update_fields=['plan', 'updated_at'])
