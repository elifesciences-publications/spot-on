# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-06-11 01:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SPTGUI', '0021_dataset_pre_ngaps'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='import_report',
            field=models.TextField(blank=True, null=True),
        ),
    ]
