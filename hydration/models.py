from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class HydrationGoal(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='hydration_goal')
    daily_goal = models.IntegerField(default=2000)  # ml

    def __str__(self):
        return self.user.username + ' — ' + str(self.daily_goal) + 'ml'


class WaterLog(models.Model):
    user      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='water_logs')
    amount    = models.IntegerField()          # ml
    date      = models.DateField()
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-logged_at']

    def __str__(self):
        return self.user.username + ' +' + str(self.amount) + 'ml (' + str(self.date) + ')'