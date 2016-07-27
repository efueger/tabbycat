# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-03 19:27
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('actionlog', '0003_auto_20160103_1927'),
        ('tournaments', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='actionlogentry',
            name='round',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tournaments.Round'),
        ),
        migrations.AddField(
            model_name='actionlogentry',
            name='tournament',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tournaments.Tournament'),
        ),
        migrations.AddField(
            model_name='actionlogentry',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]