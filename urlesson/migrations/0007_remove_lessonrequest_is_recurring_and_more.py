# Generated by Django 4.2 on 2025-06-07 18:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('urlesson', '0006_teacheravailability_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lessonrequest',
            name='is_recurring',
        ),
        migrations.RemoveField(
            model_name='lessonrequest',
            name='recurring_end_date',
        ),
        migrations.AddField(
            model_name='lessonrequest',
            name='repeat_weeks',
            field=models.PositiveIntegerField(default=1, help_text='Number of lessons'),
        ),
    ]
