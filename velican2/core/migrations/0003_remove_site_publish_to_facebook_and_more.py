# Generated by Django 4.2 on 2023-09-22 09:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_post_translation_of_alter_site_deployment_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='site',
            name='publish_to_facebook',
        ),
        migrations.RemoveField(
            model_name='site',
            name='publish_to_fediverse',
        ),
        migrations.RemoveField(
            model_name='site',
            name='publish_to_instagram',
        ),
        migrations.RemoveField(
            model_name='site',
            name='publish_to_linkedin',
        ),
        migrations.RemoveField(
            model_name='site',
            name='publish_to_twitter',
        ),
        migrations.AlterField(
            model_name='image',
            name='slug',
            field=models.CharField(help_text='Slug of matching content - must not change during its lifetime', max_length=64),
        ),
        migrations.AlterField(
            model_name='page',
            name='created',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='page',
            name='lang',
            field=models.CharField(choices=[('cs', 'cs'), ('en', 'en')], max_length=5),
        ),
        migrations.AlterField(
            model_name='page',
            name='updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='created',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='lang',
            field=models.CharField(choices=[('cs', 'cs'), ('en', 'en')], max_length=5),
        ),
        migrations.AlterField(
            model_name='post',
            name='translation_of',
            field=models.ForeignKey(blank=True, db_index=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='translations', to='core.post'),
        ),
        migrations.AlterField(
            model_name='post',
            name='updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='site',
            name='lang',
            field=models.CharField(choices=[('cs', 'cs'), ('en', 'en')], default='cs', max_length=2),
        ),
    ]