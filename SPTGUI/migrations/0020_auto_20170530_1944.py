# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-05-30 19:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SPTGUI', '0019_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='email',
            name='validation_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='date validated'),
        ),
    ]
