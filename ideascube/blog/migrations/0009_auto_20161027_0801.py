# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-27 08:01
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0008_auto_20161007_1220'),
    ]

    operations = [
        migrations.AlterField(
            model_name='content',
            name='author',
            field=models.ForeignKey(
                on_delete=models.deletion.PROTECT, to=settings.AUTH_USER_MODEL,
                verbose_name='author'),
        ),
        migrations.AlterField(
            model_name='content',
            name='published_at',
            field=models.DateTimeField(
                default=timezone.now, verbose_name='publication date'),
        ),
    ]