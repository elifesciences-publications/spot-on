# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-06-24 00:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SPTGUI', '0023_analysis_editable'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='dt',
            field=models.FloatField(blank=True, null=True),
        ),
    ]