# Generated by Django 4.2 on 2023-04-27 13:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_remove_publish_preview_publish_force_publish_purge_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='publish',
            options={'ordering': ('site', '-finished'), 'verbose_name': 'Publish', 'verbose_name_plural': 'Publish'},
        ),
    ]