# Generated by Django 4.2 on 2023-06-04 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pelican', '0004_alter_theme_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='settings',
            name='post_url_template',
            field=models.CharField(choices=[('{slug}.html', '<slug>.html'), ('{slug}/index.html', '<slug>/index.html'), ('{date:%Y}/{slug}.html', '<year>/<slug>.html'), ('{date:%Y}/{date:%b}/{slug}.html', '<year>/<month>/<slug>.html'), ('{category}/{slug}.html', '<author>/<slug>.html'), ('{category}/{slug}.html', '<category>/<slug>.html'), ('{category}/{date:%Y}/{slug}.html', '<category>/<year>/<slug>.html')], default='{slug}.html', max_length=255),
        ),
        migrations.AlterField(
            model_name='settings',
            name='show_internal_pages_author',
            field=models.BooleanField(default=False, help_text='Include authors page'),
        ),
        migrations.AlterField(
            model_name='settings',
            name='show_internal_pages_categories',
            field=models.BooleanField(default=True, help_text='Include categories page'),
        ),
        migrations.AlterField(
            model_name='settings',
            name='show_internal_pages_tags',
            field=models.BooleanField(default=True, help_text='Include tags page'),
        ),
    ]
