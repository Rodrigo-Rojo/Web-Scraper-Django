# Generated by Django 4.0.3 on 2022-03-01 20:44

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='WebScraper',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('body', models.TextField()),
                ('img', models.URLField(max_length=500)),
                ('url', models.URLField(max_length=500)),
                ('date', models.DateField(auto_now=True)),
            ],
        ),
    ]
