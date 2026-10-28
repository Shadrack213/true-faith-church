"""
Starting data: only information already confirmed on the website.
Nothing is invented. Unknown districts, branch addresses, leaders and events
are left for authorised administrators to add later in Django Admin.
Safe to run on a database that already has some of these rows.
"""
from datetime import datetime, timezone

from django.db import migrations

REGIONS = [
    ("ashanti-region", "Ashanti Region"), ("ashanti-east", "Ashanti East"), ("ashanti-west", "Ashanti West"),
    ("brong-ahafo", "Brong Ahafo"), ("brong-ahafo-east", "Brong Ahafo East"), ("brong-ahafo-west", "Brong Ahafo West"),
    ("central-region", "Central Region"), ("eastern-north", "Eastern North"), ("eastern-south", "Eastern South"),
    ("greater-accra", "Greater Accra"), ("greater-accra-east", "Greater Accra East"),
    ("greater-accra-west", "Greater Accra West"), ("western-region", "Western Region"),
    ("western-north", "Western North"), ("volta-region", "Volta Region"), ("oti-region", "Oti Region"),
    ("northern-region", "Northern Region"), ("upper-east-region", "Upper East Region"),
    ("upper-west-region", "Upper West Region"), ("bono-east-region", "Bono East Region"),
]

# Kumasi and Accra are confirmed; Asawinso is named on the Youth Impact Night flyer.
# Their regions are not verified yet, so region stays empty.
DISTRICTS = [("kumasi-district", "Kumasi District"), ("accra-district", "Accra District"),
             ("asawinso-district", "Asawinso District")]

MINISTRIES = [
    ("women-commission", "Women Commission",
     "The Women Commission encourages the women of True Faith Church International in holiness, prayer, "
     "and faithful service in the home, the church, and society."),
    ("church-administration", "Church Administration",
     "Church Administration supports the orderly running of True Faith Church International."),
    ("youth-ministry", "Youth Ministry",
     "The Youth Ministry helps young people of True Faith Church International to grow in the Word of God, "
     "Christian discipline, and faithful Sabbath worship."),
    ("evangelism-ministry", "Evangelism Ministry",
     "Preaching, practicing, and propagating the Gospel of Jesus Christ through prayer, teaching, missions, "
     "and evangelism throughout the world."),
    ("childrens-ministry", "Children's Ministry",
     "The Children's Ministry nurtures the children of True Faith Church International in the pure truth of "
     "the Kingdom of God."),
    ("prophetic-ministry", "Prophetic Ministry", ""),
    ("soul-ministry", "Soul Ministry", ""),
]


def seed(apps, schema_editor):
    Region = apps.get_model("church", "Region")
    District = apps.get_model("church", "District")
    ChurchLocation = apps.get_model("church", "ChurchLocation")
    Ministry = apps.get_model("church", "Ministry")
    Leader = apps.get_model("church", "Leader")
    Event = apps.get_model("church", "Event")

    for i, (slug, name) in enumerate(REGIONS, start=1):
        Region.objects.get_or_create(slug=slug, defaults={"name": name, "sort_order": i})
    for i, (slug, name) in enumerate(DISTRICTS, start=1):
        District.objects.get_or_create(slug=slug, defaults={"name": name, "sort_order": i})

    ChurchLocation.objects.get_or_create(
        country_code="GH", name="True Faith Church International Headquarters",
        defaults={
            "kind": "headquarters", "country_name": "Ghana", "locality": "Kwahu Praso",
            "address": "Kwahu Praso, Ghana", "postal_address": "P.O. Box 203, Ejisu",
            "phone": "+233 24 496 2073", "email": "info@truefaithchurchintl.org",
            "is_verified": True, "is_active": True, "is_public": True, "sort_order": 0,
        },
    )

    for i, (slug, name, description) in enumerate(MINISTRIES, start=1):
        Ministry.objects.get_or_create(slug=slug, defaults={
            "name": name, "description": description, "status": "published", "sort_order": i})

    Leader.objects.get_or_create(
        full_name="Apostle Thomas Adu Bempah", title="Acting General Overseer", scope="headquarters",
        defaults={"status": "published", "sort_order": 1},
    )

    # Youth Impact Night: Sat 10 Oct 2026, 10:00 PM Ghana time (= UTC)
    starts = datetime(2026, 10, 10, 22, 0, tzinfo=timezone.utc)
    Event.objects.get_or_create(
        title="Youth Impact Night", starts_at=starts, category="national",
        defaults={
            "description": "Maakro Youth Association (MAYA) presents Youth Impact Night. Guest speaker: "
                           "Apostle Sampson Koomson, Asawinso District. Theme: Isaiah 40:31.",
            "time_zone": "Africa/Accra",
            "venue": "True Faith Church Int., Maakro Branch",
            "flyer_link": "assets/images/youth-impact-night-flyer.webp",
            "image_url": "https://images.pixieset.com/572383421/3d27984c022f6cab48267cf886b74706-xlarge.JPG",
            "link_url": "https://s-kayphotos62.pixieset.com/youthimpactnight/",
            "status": "published",
            "published_at": starts,
        },
    )


class Migration(migrations.Migration):
    dependencies = [("church", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
