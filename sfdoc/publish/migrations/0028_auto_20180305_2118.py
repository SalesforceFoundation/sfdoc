# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-03-05 21:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('publish', '0027_bundle_time_last_modified'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='status',
            field=models.CharField(choices=[('N', 'New'), ('C', 'Changed'), ('D', 'Deleted')], max_length=1),
        ),
        migrations.AlterField(
            model_name='image',
            name='status',
            field=models.CharField(choices=[('N', 'New'), ('C', 'Changed'), ('D', 'Deleted')], max_length=1),
        ),
    ]
