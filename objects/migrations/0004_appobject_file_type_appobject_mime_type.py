# Generated by Django 5.0.6 on 2024-07-02 04:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('objects', '0003_appobject_size_alter_appobject_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='appobject',
            name='file_type',
            field=models.CharField(default='others', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='appobject',
            name='mime_type',
            field=models.CharField(default='N/A', max_length=50),
            preserve_default=False,
        ),
    ]
