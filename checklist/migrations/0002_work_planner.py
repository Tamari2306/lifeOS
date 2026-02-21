from django.db import migrations, models
import django.db.models.deletion
import django.conf


class Migration(migrations.Migration):
    dependencies = [
        ('checklist', '0001_initial'),
        migrations.swappable_dependency(django.conf.settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel('MonthGoal', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('year', models.IntegerField()),
            ('month', models.IntegerField()),
            ('title', models.CharField(max_length=200)),
            ('description', models.TextField(blank=True)),
            ('status', models.CharField(choices=[('active','Active'),('done','Done'),('dropped','Dropped')], default='active', max_length=10)),
            ('priority', models.CharField(choices=[('high','High'),('medium','Medium'),('low','Low')], default='medium', max_length=10)),
            ('created_at', models.DateField(auto_now_add=True)),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='month_goals', to=django.conf.settings.AUTH_USER_MODEL)),
        ], options={'ordering': ['status', '-priority', 'created_at']}),
        migrations.CreateModel('WeekTask', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('year', models.IntegerField()),
            ('week_number', models.IntegerField()),
            ('title', models.CharField(max_length=200)),
            ('notes', models.TextField(blank=True)),
            ('status', models.CharField(choices=[('todo','To Do'),('inprogress','In Progress'),('done','Done')], default='todo', max_length=15)),
            ('priority', models.CharField(choices=[('high','High'),('medium','Medium'),('low','Low')], default='medium', max_length=10)),
            ('planned_day', models.IntegerField(blank=True, choices=[(0,'Monday'),(1,'Tuesday'),(2,'Wednesday'),(3,'Thursday'),(4,'Friday'),(5,'Saturday'),(6,'Sunday')], null=True)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('month_goal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='week_tasks', to='checklist.monthgoal')),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='week_tasks', to=django.conf.settings.AUTH_USER_MODEL)),
        ], options={'ordering': ['status', 'planned_day', '-priority']}),
        migrations.CreateModel('WorkDailyItem', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('date', models.DateField()),
            ('title', models.CharField(max_length=200)),
            ('notes', models.CharField(blank=True, max_length=300)),
            ('completed', models.BooleanField(default=False)),
            ('completed_at', models.DateTimeField(blank=True, null=True)),
            ('priority', models.CharField(choices=[('high','High'),('medium','Medium'),('low','Low')], default='medium', max_length=10)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='work_daily_items', to=django.conf.settings.AUTH_USER_MODEL)),
            ('week_task', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='daily_items', to='checklist.weektask')),
        ], options={'ordering': ['completed', '-priority', 'created_at']}),
    ]