# Generated by Django 2.2.1 on 2019-05-31 07:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('publish', '0030_auto_20180313_1948'),
    ]

    operations = [
        migrations.AddField(
            model_name='bundle',
            name='description',
            field=models.CharField(default='(no description)', max_length=255),
        ),
    ]
