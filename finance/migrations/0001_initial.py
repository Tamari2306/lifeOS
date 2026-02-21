from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django.conf


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(django.conf.settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MonthlyBudget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('year', models.IntegerField()),
                ('month', models.IntegerField()),
                ('amount', models.DecimalField(max_digits=12, decimal_places=2)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='monthly_budgets', to=django.conf.settings.AUTH_USER_MODEL)),
            ],
            options={'unique_together': {('user', 'year', 'month')}},
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(max_digits=10, decimal_places=2)),
                ('category', models.CharField(max_length=20, choices=[('food','Food'),('transport','Transport'),('bills','Bills'),('shopping','Shopping'),('health','Health'),('misc','Misc')])),
                ('note', models.CharField(max_length=200, blank=True)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expenses', to=django.conf.settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-added_at']},
        ),
        migrations.CreateModel(
            name='SavingsGoal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('target_amount', models.DecimalField(max_digits=12, decimal_places=2)),
                ('saved_amount', models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ('contribution', models.DecimalField(max_digits=10, decimal_places=2)),
                ('frequency', models.CharField(max_length=10, choices=[('weekly','Weekly'),('monthly','Monthly')], default='monthly')),
                ('target_date', models.DateField(null=True, blank=True)),
                ('created_at', models.DateField(auto_now_add=True)),
                ('emoji', models.CharField(max_length=5, default='&#127937;')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='savings_goals', to=django.conf.settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SavingsDeposit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(max_digits=10, decimal_places=2)),
                ('note', models.CharField(max_length=200, blank=True)),
                ('date', models.DateField(auto_now_add=True)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('goal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deposits', to='finance.savingsgoal')),
            ],
            options={'ordering': ['-added_at']},
        ),
    ]