from django.db import migrations, models
import django.db.models.deletion
import django.conf


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(django.conf.settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel('ReadingPlan', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('book_name', models.CharField(max_length=100)),
            ('month', models.IntegerField()),
            ('year', models.IntegerField()),
            ('total_chapters', models.IntegerField(default=1)),
            ('created_at', models.DateField(auto_now_add=True)),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reading_plans', to=django.conf.settings.AUTH_USER_MODEL)),
        ], options={'unique_together': {('user', 'month', 'year')}}),
        migrations.CreateModel('ReadingLog', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('book', models.CharField(max_length=100)),
            ('chapter', models.IntegerField()),
            ('date', models.DateField()),
            ('note', models.CharField(blank=True, max_length=300)),
            ('plan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='bible.readingplan')),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reading_logs', to=django.conf.settings.AUTH_USER_MODEL)),
        ], options={'ordering': ['-date', '-chapter'], 'unique_together': {('user', 'book', 'chapter', 'date')}}),
        migrations.CreateModel('PrayerRequest', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('text', models.TextField()),
            ('status', models.CharField(choices=[('active','Active'),('answered','Answered')], default='active', max_length=10)),
            ('created_at', models.DateField(auto_now_add=True)),
            ('answered_at', models.DateField(blank=True, null=True)),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prayer_requests', to=django.conf.settings.AUTH_USER_MODEL)),
        ], options={'ordering': ['-created_at']}),
        migrations.CreateModel('Memorization', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('reference', models.CharField(max_length=100)),
            ('text', models.TextField()),
            ('mastered', models.BooleanField(default=False)),
            ('added_at', models.DateField(auto_now_add=True)),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memorizations', to=django.conf.settings.AUTH_USER_MODEL)),
        ], options={'ordering': ['-added_at']}),
    ]