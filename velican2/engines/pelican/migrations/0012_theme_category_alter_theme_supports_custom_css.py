# Generated by Django 4.2 on 2023-06-13 10:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pelican', '0011_theme_supports_custom_css_themesettings_custom_css'),
    ]

    operations = [
        migrations.AddField(
            model_name='theme',
            name='category',
            field=models.CharField(choices=[('blog', 'Blog'), ('conf', 'Conference'), ('corp', 'Company')], default='blog', max_length=4),
        ),
        migrations.AlterField(
            model_name='theme',
            name='supports_custom_css',
            field=models.BooleanField(default=False),
        ),
    ]
