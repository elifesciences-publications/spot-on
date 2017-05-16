# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-05-16 16:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SPTGUI', '0017_download_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysis',
            name='acc_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='date accessed'),
        ),
        migrations.AddField(
            model_name='analysis',
            name='mod_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='date modified'),
        ),
    ]
