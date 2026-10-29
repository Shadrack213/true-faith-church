"""
Adds the districts that already have a page on the website (tools/content/districts.json)
but were not in the database yet. District 4 to District 25 are the website's temporary
placeholders: rename them in Django Admin once the real names are confirmed, but keep
the slug, because it matches the page events-<slug>.html.
Only adds missing rows; existing districts are left exactly as they are.
"""
from django.db import migrations

DISTRICTS = [(f"district-{n}", f"District {n}", n) for n in range(4, 26)]


def add_districts(apps, schema_editor):
    District = apps.get_model("church", "District")
    for slug, name, order in DISTRICTS:
        District.objects.get_or_create(slug=slug, defaults={"name": name, "sort_order": order})


class Migration(migrations.Migration):
    dependencies = [("church", "0003_headquarters_events_map_link")]

    operations = [migrations.RunPython(add_districts, migrations.RunPython.noop)]
