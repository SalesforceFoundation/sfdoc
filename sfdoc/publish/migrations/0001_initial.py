# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-15 01:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EasyditaBundle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('easydita_id', models.CharField(max_length=255, unique=True)),
            ],
        ),
    ]
