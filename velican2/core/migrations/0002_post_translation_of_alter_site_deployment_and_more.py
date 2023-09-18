# Generated by Django 4.2 on 2023-09-18 07:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='translation_of',
            field=models.ForeignKey(blank=True, db_index=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.post'),
        ),
        migrations.AlterField(
            model_name='site',
            name='deployment',
            field=models.CharField(choices=[('caddy', 'local web server'), ('aws', 'AWS CloudFront')], default='caddy', max_length=12),
        ),
        migrations.AlterField(
            model_name='site',
            name='staff',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
    ]