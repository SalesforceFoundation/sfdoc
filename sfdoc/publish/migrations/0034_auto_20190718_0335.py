# Generated by Django 2.2.3 on 2019-07-18 03:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('publish', '0033_auto_20190713_1833'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='article',
            unique_together={('bundle', 'url_name')},
        ),
    ]