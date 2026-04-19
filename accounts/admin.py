from django.contrib import admin

from .models import UserPlan


@admin.register(UserPlan)
class UserPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'attempts_used', 'created_at', 'updated_at')
    list_filter = ('plan',)
    search_fields = ('user__email', 'user__username')
