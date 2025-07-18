# Generated by Django 4.2 on 2025-07-17 16:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('urlesson', '0011_alter_customuser_managers'),
    ]

    operations = [
        migrations.AddField(
            model_name='lessonrequest',
            name='subject',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lesson_requests', to='urlesson.subject'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(choices=[('student', 'Student'), ('teacher', 'Teacher'), ('admin', 'Admin')], max_length=10),
        ),
    ]
