from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Exercise(models.Model):
    CATEGORY_CHOICES = [
        ('Strength', 'Strength'),
        ('Cardio',   'Cardio'),
        ('Core',     'Core'),
    ]

    name         = models.CharField(max_length=100)
    category     = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Strength')
    video        = models.FileField(upload_to='videos/', blank=True, null=True)
    default_reps = models.IntegerField(default=10)
    sets         = models.IntegerField(default=3)
    description  = models.TextField(blank=True)
    created_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_exercises')

    def __str__(self):
        return self.name


class WorkoutLog(models.Model):
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_logs')
    exercise     = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='logs')
    date         = models.DateField(auto_now_add=True)
    reps_per_set = models.IntegerField(default=10)
    sets         = models.IntegerField(default=3)
    completed    = models.BooleanField(default=True)
    logged_at    = models.DateTimeField(auto_now_add=True)

    @property
    def total_reps(self):
        return self.reps_per_set * self.sets

    class Meta:
        ordering = ['-logged_at']

    def __str__(self):
        return f"{self.user.username} — {self.exercise.name} ({self.date})"
    
class WorkoutSchedule(models.Model):
    DAY_CHOICES = [
        ('mon',     'Monday'),
        ('tue',     'Tuesday'),
        ('wed',     'Wednesday'),
        ('thu',     'Thursday'),
        ('fri',     'Friday'),
        ('weekend', 'Weekend'),
        ('gym',     'Gym Day'),
    ]

    user     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='workout_schedule')
    day      = models.CharField(max_length=10, choices=DAY_CHOICES)
    name     = models.CharField(max_length=200)
    icon     = models.CharField(max_length=10, default='💪')
    sets     = models.PositiveSmallIntegerField(null=True, blank=True)
    reps     = models.PositiveSmallIntegerField(null=True, blank=True)
    duration = models.CharField(max_length=50, blank=True)
    notes    = models.CharField(max_length=300, blank=True)
    order    = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['day', 'order', 'id']

    def __str__(self):
        return f"{self.get_day_display()} — {self.name}"