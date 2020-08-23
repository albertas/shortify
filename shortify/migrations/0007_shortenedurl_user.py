# Generated by Django 3.1 on 2020-08-22 16:21

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("shortify", "0006_auto_20200820_1822"),
    ]

    operations = [
        migrations.AddField(
            model_name="shortenedurl",
            name="user",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.RESTRICT, to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
