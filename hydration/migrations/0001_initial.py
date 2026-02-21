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
            name='HydrationGoal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('daily_goal', models.IntegerField(default=2000)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='hydration_goal', to=django.conf.settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='WaterLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('amount', models.IntegerField()),
                ('date', models.DateField()),
                ('logged_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='water_logs', to=django.conf.settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-logged_at']},
        ),
    ]