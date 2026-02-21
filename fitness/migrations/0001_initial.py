from django.db import migrations, models
import django.db.models.deletion
import django.conf


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(django.conf.settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Exercise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('category', models.CharField(choices=[('Strength', 'Strength'), ('Cardio', 'Cardio'), ('Core', 'Core')], default='Strength', max_length=50)),
                ('video', models.FileField(blank=True, null=True, upload_to='videos/')),
                ('default_reps', models.IntegerField(default=10)),
                ('sets', models.IntegerField(default=3)),
                ('description', models.TextField(blank=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_exercises', to=django.conf.settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='WorkoutLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
                ('reps_per_set', models.IntegerField(default=10)),
                ('sets', models.IntegerField(default=3)),
                ('completed', models.BooleanField(default=True)),
                ('logged_at', models.DateTimeField(auto_now_add=True)),
                ('exercise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='fitness.exercise')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workout_logs', to=django.conf.settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-logged_at']},
        ),
    ]