# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-14 00:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('publish', '0018_auto_20180208_2359'),
    ]

    operations = [
        migrations.AddField(
            model_name='easyditabundle',
            name='easydita_resource_id',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
    ]
