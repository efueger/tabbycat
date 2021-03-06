# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-03 19:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Debate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bracket', models.FloatField(default=0)),
                ('room_rank', models.IntegerField(default=0)),
                ('flags', models.CharField(blank=True, max_length=100, null=True)),
                ('importance', models.IntegerField(default=2)),
                ('result_status', models.CharField(choices=[('N', 'None'), ('P', 'Postponed'), ('D', 'Draft'), ('C', 'Confirmed')], default='N', max_length=1)),
                ('ballot_in', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='DebateTeam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.CharField(choices=[('A', 'Affirmative'), ('N', 'Negative'), ('u', 'Unallocated')], max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name='TeamPositionAllocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.CharField(choices=[('A', 'Affirmative'), ('N', 'Negative'), ('u', 'Unallocated')], max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name='TeamVenuePreference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('priority', models.IntegerField()),
            ],
            options={
                'ordering': ['priority'],
            },
        ),
    ]
