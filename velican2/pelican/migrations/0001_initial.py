# Generated by Django 4.2 on 2023-04-04 13:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0002_alter_category_options_alter_post_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Theme',
            fields=[
                ('name', models.CharField(max_length=32, primary_key=True, serialize=False)),
                ('path', models.CharField(max_length=256)),
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
                ('show_page_in_menu', models.BooleanField(default=True, help_text='Display pages in menu')),
                ('show_category_in_menu', models.BooleanField(default=True, help_text='Display categories in menu')),
                ('post_url_template', models.CharField(choices=[('slug.html', '{date:%Y}/{date:%b}/{date:%d}/{slug}.html'), ('slug/index.html', '{slug}/index.html'), ('year/slug.html', '{date:%Y}/{slug}.html'), ('year/month/slug.html', '{date:%Y}/{date:%b}/{slug}.html'), ('author/slug.html', '{category}/{slug}.html'), ('category/slug.html', '{category}/{slug}.html'), ('category/year/slug.html', '{category}/{date:%Y}/{slug}.html')], max_length=255)),
                ('page_url_prefix', models.CharField(help_text="Pages URL prefix (pages urls will look like 'prefix/{slug}.html')", max_length=35)),
                ('category_url_prefix', models.CharField(help_text="Category URL prefix (pages urls will look like 'prefix/{slug}.html')", max_length=35)),
                ('author_url_prefix', models.CharField(help_text="Author URL prefix (pages urls will look like 'prefix/{slug}.html')", max_length=35)),
                ('facebook', models.CharField(max_length=128, null=True)),
                ('twitter', models.CharField(max_length=128, null=True)),
                ('linkedin', models.CharField(max_length=128, null=True)),
                ('github', models.CharField(max_length=128, null=True)),
                ('site', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='pelican', to='core.site')),
                ('theme', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='pelican.theme')),
            ],
            options={
                'verbose_name': 'Settings',
                'verbose_name_plural': 'Settings',
            },
        ),
    ]