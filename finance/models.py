from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class MonthlyBudget(models.Model):
    """The total amount a user has available for the month."""
    user   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='monthly_budgets')
    year   = models.IntegerField()
    month  = models.IntegerField()  # 1-12
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ('user', 'year', 'month')

    def __str__(self):
        return self.user.username + ' — ' + str(self.month) + '/' + str(self.year) + ' budget: ' + str(self.amount)


class Expense(models.Model):
    CATEGORIES = [
        ('food',       'Food'),
        ('transport',  'Transport'),
        ('bills',      'Bills'),
        ('shopping',   'Shopping'),
        ('health',     'Health'),
        ('misc',       'Misc'),
    ]
    user     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    amount   = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    note     = models.CharField(max_length=200, blank=True)
    date     = models.DateField(default=timezone.now)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']

    def __str__(self):
        return self.user.username + ' — ' + self.category + ': ' + str(self.amount)


class SavingsGoal(models.Model):
    FREQUENCY = [
        ('weekly',  'Weekly'),
        ('monthly', 'Monthly'),
    ]
    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='savings_goals')
    name            = models.CharField(max_length=100)
    target_amount   = models.DecimalField(max_digits=12, decimal_places=2)
    saved_amount    = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    contribution    = models.DecimalField(max_digits=10, decimal_places=2)  # amount per period
    frequency       = models.CharField(max_length=10, choices=FREQUENCY, default='monthly')
    target_date     = models.DateField(null=True, blank=True)
    created_at      = models.DateField(auto_now_add=True)
    emoji           = models.CharField(max_length=5, default='&#127937;')

    @property
    def pct(self):
        if self.target_amount == 0:
            return 0
        return min(100, int(float(self.saved_amount) / float(self.target_amount) * 100))

    @property
    def remaining(self):
        return max(0, float(self.target_amount) - float(self.saved_amount))

    def __str__(self):
        return self.user.username + ' — ' + self.name


class SavingsDeposit(models.Model):
    """Each time a user adds money to a savings goal."""
    goal     = models.ForeignKey(SavingsGoal, on_delete=models.CASCADE, related_name='deposits')
    amount   = models.DecimalField(max_digits=10, decimal_places=2)
    note     = models.CharField(max_length=200, blank=True)
    date     = models.DateField(auto_now_add=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']