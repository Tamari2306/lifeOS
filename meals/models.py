from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class MealEntry(models.Model):
    MEAL_TYPE = [
        ('breakfast', 'Breakfast'),
        ('lunch',     'Lunch'),
        ('dinner',    'Dinner'),
        ('snack',     'Snack'),
    ]
    user     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_entries')
    date     = models.DateField()
    meal_type = models.CharField(max_length=15, choices=MEAL_TYPE)
    name     = models.CharField(max_length=200)
    calories = models.IntegerField(default=0)
    protein  = models.IntegerField(default=0)   # grams
    carbs    = models.IntegerField(default=0)    # grams
    fat      = models.IntegerField(default=0)    # grams
    notes    = models.CharField(max_length=300, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'meal_type']

    def __str__(self):
        return f"{self.user.username} — {self.meal_type}: {self.name} ({self.date})"


class NutritionGoal(models.Model):
    user     = models.OneToOneField(User, on_delete=models.CASCADE, related_name='nutrition_goal')
    calories = models.IntegerField(default=1800)
    protein  = models.IntegerField(default=120)
    carbs    = models.IntegerField(default=180)
    fat      = models.IntegerField(default=60)

    def __str__(self):
        return f"{self.user.username} nutrition goals"


class RecipeIdea(models.Model):
    """User's saved meal ideas / recipes."""
    CATEGORY = [
        ('breakfast','Breakfast'),('lunch','Lunch'),('dinner','Dinner'),
        ('snack','Snack'),('drink','Drink'),
    ]
    user     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipe_ideas')
    name     = models.CharField(max_length=200)
    category = models.CharField(max_length=15, choices=CATEGORY, default='lunch')
    ingredients = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    calories = models.IntegerField(default=0)
    protein  = models.IntegerField(default=0)
    prep_time = models.IntegerField(default=0)  # minutes
    added_at = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return self.name