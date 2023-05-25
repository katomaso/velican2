# Generated by Django 4.2 on 2023-04-17 09:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ThemeSource',
            fields=[
                ('url', models.CharField(max_length=256, primary_key=True, serialize=False)),
                ('multiple', models.BooleanField(default=False, help_text='Check when the repository contains multiple themes. You cannot install them easily then')),
                ('updated', models.DateTimeField(blank=True, null=True)),
                ('log', models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Theme',
            fields=[
                ('name', models.CharField(blank=True, help_text='Must be set explicitely for Multi Theme Source', max_length=32, primary_key=True, serialize=False)),
                ('mapping', models.TextField(blank=True, help_text='Jinja code to define necessary variables for the theme', null=True)),
                ('installed', models.BooleanField(default=False)),
                ('updated', models.DateTimeField(auto_now_add=True)),
                ('log', models.TextField(null=True)),
                ('source', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='themes', to='pelican.themesource')),
            ],
            options={
                'verbose_name': 'Theme',
                'verbose_name_plural': 'Themes',
            },
        ),
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('show_pages_in_menu', models.BooleanField(default=True, help_text='Display pages in menu')),
                ('show_categories_in_menu', models.BooleanField(default=True, help_text='Display categories in menu')),
                ('post_url_template', models.CharField(choices=[('{slug}.html', '<slug>.html'), ('{slug}/index.html', '<slug>/index.html'), ('{date:%Y}/{slug}.html', '<year>/<slug>.html'), ('{date:%Y}/{date:%b}/{slug}.html', '<year>/<month>/<slug>.html'), ('{category}/{slug}.html', '<author>/<slug>.html'), ('{category}/{slug}.html', '<category>/<slug>.html'), ('{category}/{date:%Y}/{slug}.html', '<category>/<year>/<slug>.html')], default='{slug}.html', max_length=255)),
                ('page_url_prefix', models.CharField(blank=True, default='', help_text="Pages URL prefix (pages urls will look like 'prefix/{slug}.html')", max_length=35)),
                ('category_url_prefix', models.CharField(default='category', help_text="Category URL prefix (pages urls will look like 'prefix/{slug}.html')", max_length=35)),
                ('author_url_prefix', models.CharField(default='author', help_text="Author URL prefix (pages urls will look like 'prefix/{slug}.html')", max_length=35)),
                ('facebook', models.CharField(blank=True, max_length=128, null=True)),
                ('twitter', models.CharField(blank=True, max_length=128, null=True)),
                ('linkedin', models.CharField(blank=True, max_length=128, null=True)),
                ('github', models.CharField(blank=True, max_length=128, null=True)),
                ('site', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='pelican', to='core.site')),
                ('theme', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='pelican.theme')),
            ],
            options={
                'verbose_name': 'Settings',
                'verbose_name_plural': 'Settings',
            },
        ),
    ]
