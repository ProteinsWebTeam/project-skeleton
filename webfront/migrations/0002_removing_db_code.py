# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-05-02 11:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('webfront', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='database',
            name='code',
        ),
    ]
