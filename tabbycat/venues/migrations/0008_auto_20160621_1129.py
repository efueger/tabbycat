# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-21 11:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('venues', '0007_adjudicatorvenueconstraint_divisionvenueconstraint_institutionvenueconstraint_teamvenueconstraint'),
    ]

    operations = [
        migrations.AlterField(
            model_name='divisionvenueconstraint',
            name='division',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='divisions.Division'),
        ),
    ]