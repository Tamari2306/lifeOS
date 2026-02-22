from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class ChecklistItem(models.Model):
    PRIORITY = [('high','High'),('medium','Medium'),('low','Low')]
    CATEGORY = [
        ('personal','Personal'),('work','Work'),('health','Health'),
        ('spiritual','Spiritual'),('finance','Finance'),('other','Other'),
    ]

    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='checklist_items')
    text         = models.CharField(max_length=300)
    category     = models.CharField(max_length=20, choices=CATEGORY, default='personal')
    priority     = models.CharField(max_length=10, choices=PRIORITY, default='medium')
    date         = models.DateField()
    completed    = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    order        = models.IntegerField(default=0)

    class Meta:
        ordering = ['completed', 'order', '-created_at']

    def __str__(self):
        return f"{self.user.username} — {self.text[:50]}"


class DayReflection(models.Model):
    RATING = [(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5')]

    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reflections')
    date            = models.DateField(unique=True)
    what_went_well  = models.TextField(blank=True)
    what_to_improve = models.TextField(blank=True)
    grateful_for    = models.TextField(blank=True)
    mood_rating     = models.IntegerField(choices=RATING, default=3)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']


# ── WORK PLANNER ─────────────────────────────────────────────────────────────

class MonthGoal(models.Model):
    """Big picture goals for a specific month."""
    STATUS = [('active','Active'),('done','Done'),('dropped','Dropped')]

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='month_goals')
    year       = models.IntegerField()
    month      = models.IntegerField()   # 1-12
    title      = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status     = models.CharField(max_length=10, choices=STATUS, default='active')
    priority   = models.CharField(max_length=10, choices=[('high','High'),('medium','Medium'),('low','Low')], default='medium')
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['status', '-priority', 'created_at']

    def __str__(self):
        return f"{self.user.username} — {self.month}/{self.year}: {self.title}"


class WeekTask(models.Model):
    """Planned tasks for a specific ISO week."""
    STATUS = [('todo','To Do'),('inprogress','In Progress'),('done','Done')]
    DAY_OF_WEEK = [
        (0,'Monday'),(1,'Tuesday'),(2,'Wednesday'),
        (3,'Thursday'),(4,'Friday'),(5,'Saturday'),(6,'Sunday'),
    ]

    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='week_tasks')
    year         = models.IntegerField()
    week_number  = models.IntegerField()   # ISO week 1-53
    title        = models.CharField(max_length=200)
    notes        = models.TextField(blank=True)
    status       = models.CharField(max_length=15, choices=STATUS, default='todo')
    priority     = models.CharField(max_length=10, choices=[('high','High'),('medium','Medium'),('low','Low')], default='medium')
    planned_day  = models.IntegerField(choices=DAY_OF_WEEK, null=True, blank=True)  # which day in the week
    month_goal   = models.ForeignKey(MonthGoal, on_delete=models.SET_NULL, null=True, blank=True, related_name='week_tasks')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['status', 'planned_day', '-priority']

    def __str__(self):
        return f"{self.user.username} W{self.week_number}/{self.year}: {self.title}"


class WorkDailyItem(models.Model):
    """Work-specific daily tasks (separate from personal checklist)."""
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='work_daily_items')
    date         = models.DateField()
    title        = models.CharField(max_length=200)
    notes        = models.CharField(max_length=300, blank=True)
    completed    = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    priority     = models.CharField(max_length=10, choices=[('high','High'),('medium','Medium'),('low','Low')], default='medium')
    week_task    = models.ForeignKey(WeekTask, on_delete=models.SET_NULL, null=True, blank=True, related_name='daily_items')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['completed', '-priority', 'created_at']

    def __str__(self):
        return f"{self.user.username} — work {self.date}: {self.title}"

class RoutineTask(models.Model):
    """A predefined task the user wants to do every day."""

    CATEGORY_CHOICES = [
        ('health',    '💪 Health'),
        ('spiritual', '✝️ Spiritual'),
        ('personal',  '👤 Personal'),
        ('work',      '💼 Work'),
        ('finance',   '💰 Finance'),
        ('other',     '📦 Other'),
    ]
    TIME_CHOICES = [
        ('morning',   '🌅 Morning'),
        ('afternoon', '☀️ Afternoon'),
        ('evening',   '🌙 Evening'),
        ('anytime',   '🔄 Anytime'),
    ]

    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='routine_tasks')
    title       = models.CharField(max_length=255)
    category    = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='personal')
    time_of_day = models.CharField(max_length=20, choices=TIME_CHOICES, default='anytime')
    order       = models.PositiveIntegerField(default=0)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.title


class RoutineLog(models.Model):
    """Tracks whether a RoutineTask was completed on a specific date."""

    routine_task = models.ForeignKey(RoutineTask, on_delete=models.CASCADE, related_name='logs')
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='routine_logs')
    date         = models.DateField()
    completed    = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('routine_task', 'date')
        ordering = ['routine_task__order', 'routine_task__created_at']

    def __str__(self):
        return f"{self.routine_task.title} — {self.date} ({'✓' if self.completed else '○'})"
