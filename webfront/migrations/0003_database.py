# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-02-16 15:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webfront', '0002_including_prot_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='Database',
            fields=[
                ('name', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('code', models.CharField(max_length=1)),
                ('name_long', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('version', models.CharField(max_length=100)),
                ('release_date', models.DateField()),
                ('type', models.CharField(max_length=100)),
            ],
        ),
    ]
