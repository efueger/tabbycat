# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-08-23 10:51
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('breakqual', '0009_auto_20160809_1054'),
    ]

    operations = [
        migrations.AlterField(
            model_name='breakcategory',
            name='break_size',
            field=models.IntegerField(help_text='Number of breaking teams in this category', validators=[django.core.validators.MinValueValidator(2)]),
        ),
    ]
