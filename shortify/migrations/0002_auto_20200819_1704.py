from django.db import migrations


def create_default_site(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    Site.objects.all().delete()
    default_site = "localhost:8000"
    Site.objects.create(domain=default_site, name=default_site)


class Migration(migrations.Migration):

    dependencies = [
        ("shortify", "0001_initial"),
        ("sites", "0002_alter_domain_unique"),
    ]

    operations = [
        migrations.RunPython(create_default_site),
    ]
