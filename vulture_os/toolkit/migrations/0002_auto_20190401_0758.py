# Generated by Django 2.1.3 on 2019-04-01 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('toolkit', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='header',
            name='match',
            field=models.TextField(default='matching regex', help_text=''),
        ),
        migrations.AlterField(
            model_name='header',
            name='replace',
            field=models.TextField(default='replacement pattern', help_text=''),
        ),
    ]
