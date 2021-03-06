# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-25 15:05
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Analysis',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url_basename', models.CharField(max_length=200)),
                ('pub_date', models.DateTimeField(verbose_name='date published')),
                ('name', models.CharField(max_length=200)),
                ('description', models.CharField(max_length=2000)),
            ],
        ),
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.CharField(max_length=2000)),
                ('analysis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='SPTGUI.Analysis')),
            ],
        ),
    ]
