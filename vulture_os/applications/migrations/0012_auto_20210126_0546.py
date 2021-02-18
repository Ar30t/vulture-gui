# Generated by Django 2.1.3 on 2021-01-26 05:46

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_auto_20210126_0546'),
        ('applications', '0011_auto_20200915_1600'),
    ]

    operations = [
        migrations.DeleteModel(
            name='portalTemplate',
        ),
        migrations.DeleteModel(
            name='TemplateImage',
        ),
        migrations.AlterField(
            model_name='server',
            name='weight',
            field=models.PositiveIntegerField(default=1, help_text='', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(256)]),
        ),
    ]