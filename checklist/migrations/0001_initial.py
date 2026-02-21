from django.db import migrations, models
import django.db.models.deletion
import django.conf


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(django.conf.settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel('ChecklistItem', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('text', models.CharField(max_length=300)),
            ('category', models.CharField(choices=[('personal','Personal'),('work','Work'),('health','Health'),('spiritual','Spiritual'),('finance','Finance'),('other','Other')], default='personal', max_length=20)),
            ('priority', models.CharField(choices=[('high','High'),('medium','Medium'),('low','Low')], default='medium', max_length=10)),
            ('date', models.DateField()),
            ('completed', models.BooleanField(default=False)),
            ('completed_at', models.DateTimeField(blank=True, null=True)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('order', models.IntegerField(default=0)),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checklist_items', to=django.conf.settings.AUTH_USER_MODEL)),
        ], options={'ordering': ['completed', 'order', '-created_at']}),
        migrations.CreateModel('DayReflection', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
            ('date', models.DateField(unique=True)),
            ('what_went_well', models.TextField(blank=True)),
            ('what_to_improve', models.TextField(blank=True)),
            ('grateful_for', models.TextField(blank=True)),
            ('mood_rating', models.IntegerField(choices=[(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5')], default=3)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reflections', to=django.conf.settings.AUTH_USER_MODEL)),
        ], options={'ordering': ['-date']}),
    ]