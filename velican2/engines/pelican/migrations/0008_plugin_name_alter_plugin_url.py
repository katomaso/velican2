# Generated by Django 4.2 on 2023-06-04 12:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pelican', '0007_plugin_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='plugin',
            name='name',
            field=models.CharField(default='', max_length=32),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='plugin',
            name='url',
            field=models.CharField(blank=True, help_text='Null for built-in plugins', max_length=265, null=True),
        ),
    ]