# Generated by Django 5.0.6 on 2024-06-27 22:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='appuser',
            name='is_email_verified',
            field=models.BooleanField(default=False),
        ),
    ]
