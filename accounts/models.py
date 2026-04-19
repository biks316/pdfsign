from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserPlan(models.Model):
    PLAN_FREE = 'free'
    PLAN_SILVER = 'silver'
    PLAN_GOLD = 'gold'
    PLAN_CHOICES = (
        (PLAN_FREE, 'Free'),
        (PLAN_SILVER, 'Silver'),
        (PLAN_GOLD, 'Gold'),
    )
    PLAN_LIMITS = {
        PLAN_FREE: 5,
        PLAN_SILVER: 7,
        PLAN_GOLD: 10,
    }

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_plan',
    )
    plan = models.CharField(max_length=12, choices=PLAN_CHOICES, default=PLAN_FREE)
    attempts_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-updated_at',)

    @property
    def max_attempts(self) -> int:
        return self.PLAN_LIMITS.get(self.plan, self.PLAN_LIMITS[self.PLAN_FREE])

    @property
    def attempts_left(self) -> int:
        return max(0, self.max_attempts - self.attempts_used)

    def can_attempt(self) -> bool:
        return self.attempts_used < self.max_attempts

    def register_attempt(self) -> bool:
        if not self.can_attempt():
            return False
        self.attempts_used += 1
        self.save(update_fields=['attempts_used', 'updated_at'])
        return True


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_user_plan(sender, instance, created, **kwargs):
    if created:
        UserPlan.objects.get_or_create(user=instance)
