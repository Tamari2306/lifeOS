from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django.conf


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(django.conf.settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel('NutritionGoal', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('calories', models.IntegerField(default=1800)),
            ('protein', models.IntegerField(default=120)),
            ('carbs', models.IntegerField(default=180)),
            ('fat', models.IntegerField(default=60)),
            ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='nutrition_goal', to=django.conf.settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel('MealEntry', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('date', models.DateField()),
            ('meal_type', models.CharField(choices=[('breakfast','Breakfast'),('lunch','Lunch'),('dinner','Dinner'),('snack','Snack')], max_length=15)),
            ('name', models.CharField(max_length=200)),
            ('calories', models.IntegerField(default=0)),
            ('protein', models.IntegerField(default=0)),
            ('carbs', models.IntegerField(default=0)),
            ('fat', models.IntegerField(default=0)),
            ('notes', models.CharField(blank=True, max_length=300)),
            ('added_at', models.DateTimeField(auto_now_add=True)),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='meal_entries', to=django.conf.settings.AUTH_USER_MODEL)),
        ], options={'ordering': ['date', 'meal_type']}),
        migrations.CreateModel('RecipeIdea', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('name', models.CharField(max_length=200)),
            ('category', models.CharField(choices=[('breakfast','Breakfast'),('lunch','Lunch'),('dinner','Dinner'),('snack','Snack'),('drink','Drink')], default='lunch', max_length=15)),
            ('ingredients', models.TextField(blank=True)),
            ('instructions', models.TextField(blank=True)),
            ('calories', models.IntegerField(default=0)),
            ('protein', models.IntegerField(default=0)),
            ('prep_time', models.IntegerField(default=0)),
            ('added_at', models.DateField(auto_now_add=True)),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipe_ideas', to=django.conf.settings.AUTH_USER_MODEL)),
        ], options={'ordering': ['category', 'name']}),
    ]