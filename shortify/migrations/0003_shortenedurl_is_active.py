# Generated by Django 3.1 on 2020-08-19 17:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shortify", "0002_auto_20200819_1704"),
    ]

    operations = [
        migrations.AddField(
            model_name="shortenedurl", name="is_active", field=models.BooleanField(default=True),
        ),
    ]
