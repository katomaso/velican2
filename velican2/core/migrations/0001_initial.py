# Generated by Django 4.2 on 2023-04-17 09:25

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import re
import velican2.core.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(db_index=True, help_text='Example: example.com', max_length=32, validators=[django.core.validators.RegexValidator(regex='^([a-zA-Z0-9_\\-]+\\.?)+$')])),
                ('path', models.CharField(blank=True, default='', help_text='Fill only if your site is under a path (e.g. "/blog")', max_length=32, validators=[django.core.validators.RegexValidator(regex='^([a-zA-Z0-9_\\-]+/?)*$')])),
                ('lang', models.CharField(choices=[('cs_CZ', 'cs'), ('en_US', 'en')], max_length=48)),
                ('timezone', models.CharField(default='Europe/Prague', max_length=128)),
                ('title', models.CharField(max_length=128, null=True)),
                ('subtitle', models.CharField(max_length=128, null=True)),
                ('logo', models.ImageField(blank=True, null=True, upload_to=velican2.core.models.site_logo_upload)),
                ('allow_crawlers', models.BooleanField(default=True, help_text='Allow search engines to index this page')),
                ('allow_training', models.BooleanField(default=True, help_text='Allow AI engines to index this page')),
                ('engine', models.CharField(choices=[('pelican', 'Pelican')], default='pelican', max_length=12)),
                ('deployment', models.CharField(choices=[('caddy', 'local Caddy server')], default='caddy', max_length=12)),
                ('secure', models.BooleanField(default=True, help_text='The site is served via secured connection https')),
                ('staff', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Site',
                'verbose_name_plural': 'Sites',
                'unique_together': {('domain', 'path')},
            },
        ),
        migrations.CreateModel(
            name='Publish',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('preview', models.BooleanField(default=False)),
                ('started', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('finished', models.DateTimeField(null=True)),
                ('success', models.BooleanField(null=True)),
                ('message', models.CharField(max_length=512)),
                ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.site')),
            ],
            options={
                'verbose_name': 'Publish',
                'verbose_name_plural': 'Publish',
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.CharField(max_length=32, validators=[django.core.validators.RegexValidator(re.compile('^[-\\w]+\\Z'), 'Enter a valid “slug” consisting of Unicode letters, numbers, underscores, or hyphens.', 'invalid')])),
                ('name', models.CharField(max_length=32)),
                ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.site')),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
                'unique_together': {('site', 'slug')},
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.CharField(max_length=64, validators=[django.core.validators.RegexValidator(re.compile('^[-\\w]+\\Z'), 'Enter a valid “slug” consisting of Unicode letters, numbers, underscores, or hyphens.', 'invalid')])),
                ('title', models.CharField(max_length=128)),
                ('lang', models.CharField(choices=[('cs_CZ', 'cs'), ('en_US', 'en')], max_length=5)),
                ('content', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('description', models.TextField()),
                ('punchline', models.TextField(blank=True, help_text='Punchline for social media. Defaults to description.')),
                ('draft', models.BooleanField(default=True)),
                ('author', models.ForeignKey(db_index=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('category', models.ForeignKey(db_index=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.category')),
                ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.site')),
            ],
            options={
                'verbose_name': 'Post',
                'verbose_name_plural': 'Posts',
                'unique_together': {('site', 'slug', 'lang')},
            },
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.CharField(max_length=64, validators=[django.core.validators.RegexValidator(re.compile('^[-\\w]+\\Z'), 'Enter a valid “slug” consisting of Unicode letters, numbers, underscores, or hyphens.', 'invalid')])),
                ('title', models.CharField(max_length=128)),
                ('lang', models.CharField(choices=[('cs_CZ', 'cs'), ('en_US', 'en')], max_length=5)),
                ('content', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.site')),
            ],
            options={
                'verbose_name': 'Page',
                'verbose_name_plural': 'Pages',
                'unique_together': {('site', 'slug', 'lang')},
            },
        ),
    ]
