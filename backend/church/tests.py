"""
API tests. Run with:  python manage.py test church
(Needs a PostgreSQL DATABASE_URL whose user may create a test database.)
"""
import io
import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth.models import Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart
from django.utils import timezone
from PIL import Image

from .models import ChurchLocation, District, Event, Leader, Ministry, Region

MEDIA = tempfile.mkdtemp(prefix="tfci-test-media-")


def image_file(fmt="PNG", name="flyer.png", size=(40, 40)):
    buf = io.BytesIO()
    Image.new("RGB", size, (176, 6, 31)).save(buf, fmt)
    return SimpleUploadedFile(name, buf.getvalue(), content_type=f"image/{fmt.lower()}")


@override_settings(MEDIA_ROOT=MEDIA, STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class ApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        cls.ae = Region.objects.get(slug="ashanti-east")
        cls.central = Region.objects.get(slug="central-region")
        cls.kumasi = District.objects.get(slug="kumasi-district")
        mk = lambda **kw: Event.objects.create(**kw)
        cls.nat_up = mk(title="National Convention", category="national", starts_at=now + timedelta(days=20), status="published")
        cls.nat_draft = mk(title="Secret national draft", category="national", starts_at=now + timedelta(days=5), status="draft")
        cls.nat_arch = mk(title="Archived national", category="national", starts_at=now - timedelta(days=90), status="archived")
        cls.ae_up = mk(title="Ashanti East Revival", category="regional", region=cls.ae, starts_at=now + timedelta(days=10), status="published")
        cls.ae_draft = mk(title="Ashanti East draft", category="regional", region=cls.ae, starts_at=now + timedelta(days=3), status="draft")
        cls.central_past = mk(title="Central Convention", category="regional", region=cls.central, starts_at=now - timedelta(days=30), status="published")
        cls.kumasi_past = mk(title="Kumasi District Rally", category="district", district=cls.kumasi, starts_at=now - timedelta(days=2), status="published")
        ChurchLocation.objects.create(name="Berlin Branch", kind="international_branch", country_code="DE", country_name="Germany",
                                      locality="Berlin", is_verified=True, is_public=True)
        ChurchLocation.objects.create(name="Munich (unconfirmed)", kind="international_branch", country_code="DE", country_name="Germany",
                                      is_verified=False, is_public=False)
        ChurchLocation.objects.create(name="Closed Branch", kind="ghana_branch", country_code="GH", country_name="Ghana",
                                      is_verified=True, is_public=True, is_active=False)
        Ministry.objects.create(slug="draft-ministry", name="Draft Ministry", status="draft")
        Leader.objects.create(full_name="Draft Leader", title="Leader", scope="district", status="draft")

        cls.member = User.objects.create_user("member", password="x" * 16)
        cls.staff_noperm = User.objects.create_user("staffnoperm", password="x" * 16, is_staff=True)
        cls.editor = User.objects.create_user("editor", password="x" * 16, is_staff=True)
        cls.editor.user_permissions.add(*Permission.objects.filter(
            content_type__app_label="church", codename__in=["add_event", "change_event", "delete_event", "view_event"]))

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def titles(self, url):
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200, r.content)
        return [e["title"] for e in r.json()["results"]]

    # ---- seed data and basics ------------------------------------------
    def test_seed_data(self):
        self.assertEqual(Region.objects.count(), 20)
        self.assertEqual(District.objects.count(), 3)
        self.assertFalse(District.objects.filter(region__isnull=False).exists(), "no unverified district-region links")
        self.assertEqual(Ministry.objects.filter(status="published").count(), 7)
        self.assertTrue(Event.objects.filter(title="Youth Impact Night", status="published").exists())

    def test_health(self):
        r = self.client.get("/api/health/")
        self.assertEqual(r.json(), {"status": "ok", "database": "ok"})

    def test_api_root_and_unknown_route(self):
        self.assertEqual(self.client.get("/api/").status_code, 200)
        r = self.client.get("/api/does-not-exist/")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json(), {"detail": "Not found."})

    def admin_response(self, enabled):
        """GET /admin/ with DJANGO_ADMIN_ENABLED forced on or off, independent of backend/.env.
        config/urls.py reads the setting when it is loaded, so it is reloaded for each case."""
        import importlib

        import config.urls
        from django.urls import clear_url_caches

        try:
            with self.settings(ADMIN_ENABLED=enabled):
                importlib.reload(config.urls)
                clear_url_caches()
                return self.client.get("/admin/")
        finally:
            importlib.reload(config.urls)  # back to the real setting
            clear_url_caches()

    def test_admin_switched_off(self):
        self.assertEqual(self.admin_response(False).status_code, 404)

    def test_admin_switched_on_asks_for_login(self):
        r = self.admin_response(True)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/admin/login/", r["Location"])

    # ---- events: visibility and filtering --------------------------------
    def test_anonymous_sees_only_published(self):
        titles = self.titles("/api/events/?page_size=200")
        self.assertNotIn("Secret national draft", titles)
        self.assertNotIn("Ashanti East draft", titles)
        self.assertNotIn("Archived national", titles)
        self.assertIn("Youth Impact Night", titles)
        self.assertEqual(self.client.get(f"/api/events/{self.nat_draft.id}/").status_code, 404)
        self.assertEqual(self.client.get(f"/api/events/{self.nat_arch.id}/").status_code, 404)

    def test_category_routes(self):
        self.assertEqual(sorted(self.titles("/api/events/national/")), ["National Convention", "Youth Impact Night"])
        self.assertEqual(sorted(self.titles("/api/events/regional/")), ["Ashanti East Revival", "Central Convention"])
        self.assertEqual(self.titles("/api/events/district/"), ["Kumasi District Rally"])

    def test_region_and_district_filters(self):
        self.assertEqual(self.titles("/api/events/?category=regional&region=ashanti-east"), ["Ashanti East Revival"])
        self.assertEqual(self.titles("/api/events/regional/?region=central-region"), ["Central Convention"])
        self.assertEqual(self.titles("/api/events/district/?district=kumasi-district"), ["Kumasi District Rally"])
        self.assertEqual(self.titles("/api/events/?region=volta-region"), [])

    def test_when_filter(self):
        self.assertEqual(self.titles("/api/events/national/?when=upcoming"), ["National Convention"])
        self.assertEqual(self.titles("/api/events/national/?when=past"), ["Youth Impact Night"])

    def test_invalid_filters_return_400(self):
        r = self.client.get("/api/events/?category=weekly")
        self.assertEqual(r.status_code, 400)
        self.assertIn("category", r.json())
        self.assertEqual(self.client.get("/api/events/?when=soon").status_code, 400)
        self.assertEqual(self.client.get("/api/church-locations/?country=Ghana").status_code, 400)

    def test_event_fields_and_pagination(self):
        r = self.client.get("/api/events/national/?page_size=1").json()
        self.assertEqual(r["count"], 2)
        self.assertIsNotNone(r["next"])
        ev = self.client.get("/api/events/national/?when=past").json()["results"][0]
        for field in ["title", "category", "starts_at", "time_zone", "venue", "flyer_url", "image_url", "link_url",
                      "region_slug", "district_slug"]:
            self.assertIn(field, ev)
        self.assertEqual(ev["flyer_url"], "assets/images/youth-impact-night-flyer.webp")
        self.assertNotIn("flyer", ev)  # upload field is write-only

    # ---- other public endpoints ------------------------------------------
    def test_regions_and_districts(self):
        self.assertEqual(self.client.get("/api/regions/?page_size=200").json()["count"], 20)
        self.assertEqual(self.client.get("/api/regions/ashanti-east/").json()["name"], "Ashanti East")
        self.assertEqual(self.client.get("/api/districts/").json()["count"], 3)
        District.objects.filter(slug="kumasi-district").update(region=self.ae)
        self.assertEqual([d["slug"] for d in self.client.get("/api/districts/?region=ashanti-east").json()["results"]],
                         ["kumasi-district"])

    def test_church_locations_only_verified_public_active(self):
        names = [l["name"] for l in self.client.get("/api/church-locations/").json()["results"]]
        self.assertEqual(sorted(names), ["Berlin Branch", "True Faith Church International Headquarters"])
        de = self.client.get("/api/church-locations/?country=DE,NL").json()["results"]
        self.assertEqual([l["name"] for l in de], ["Berlin Branch"])
        gh = self.client.get("/api/church-locations/?country=GH&exclude_kind=headquarters").json()["results"]
        self.assertEqual(gh, [])

    def test_ministries_and_leadership_hide_drafts(self):
        self.assertEqual(self.client.get("/api/ministries/").json()["count"], 7)
        leaders = self.client.get("/api/leadership/").json()["results"]
        self.assertEqual([l["full_name"] for l in leaders], ["Apostle Thomas Adu Bempah"])

    # ---- writes are protected ---------------------------------------------
    def test_anonymous_cannot_write(self):
        body = {"title": "Hack", "category": "national", "starts_at": timezone.now().isoformat(), "status": "published"}
        self.assertEqual(self.client.post("/api/events/", body, content_type="application/json").status_code, 403)
        self.assertEqual(self.client.patch(f"/api/events/{self.nat_up.id}/", {"title": "x"}, content_type="application/json").status_code, 403)
        self.assertEqual(self.client.put(f"/api/events/{self.nat_up.id}/", body, content_type="application/json").status_code, 403)
        self.assertEqual(self.client.delete(f"/api/events/{self.nat_up.id}/").status_code, 403)
        self.assertEqual(self.client.post("/api/regions/", {"slug": "x", "name": "X"}, content_type="application/json").status_code, 403)
        self.assertEqual(self.client.delete("/api/church-locations/1/").status_code, 403)
        self.assertEqual(self.client.patch("/api/ministries/youth-ministry/", {"name": "x"}, content_type="application/json").status_code, 403)
        self.assertEqual(self.client.post("/api/leadership/", {"full_name": "X", "title": "Y", "scope": "zone"}, content_type="application/json").status_code, 403)
        self.assertEqual(Event.objects.get(pk=self.nat_up.pk).title, "National Convention")

    def test_signed_in_non_staff_and_staff_without_permission_cannot_write(self):
        body = {"title": "Nope", "category": "national", "starts_at": timezone.now().isoformat()}
        for user in (self.member, self.staff_noperm):
            self.client.force_login(user)
            self.assertEqual(self.client.post("/api/events/", body, content_type="application/json").status_code, 403)
            self.assertNotIn("Secret national draft", self.titles("/api/events/?page_size=200") if not user.is_staff else ["-"])
        self.client.logout()

    def test_editor_can_create_publish_and_sees_drafts(self):
        self.client.force_login(self.editor)
        self.assertIn("Secret national draft", self.titles("/api/events/?page_size=200"))
        r = self.client.post("/api/events/", {"title": "Editor event", "category": "regional", "region": "ashanti-east",
                                               "starts_at": (timezone.now() + timedelta(days=7)).isoformat()},
                             content_type="application/json")
        self.assertEqual(r.status_code, 201, r.content)
        ev = Event.objects.get(title="Editor event")
        self.assertEqual(ev.created_by, self.editor)
        self.assertEqual(ev.status, "draft")
        r = self.client.patch(f"/api/events/{ev.id}/", {"status": "published"}, content_type="application/json")
        self.assertEqual(r.status_code, 200)
        self.assertIsNotNone(Event.objects.get(pk=ev.pk).published_at)

    def test_editor_input_is_validated(self):
        self.client.force_login(self.editor)
        now = timezone.now()
        bad = [
            {"title": "No region", "category": "regional", "starts_at": now.isoformat()},
            {"title": "National with region", "category": "national", "region": "ashanti-east", "starts_at": now.isoformat()},
            {"title": "Bad dates", "category": "national", "starts_at": now.isoformat(), "ends_at": (now - timedelta(days=1)).isoformat()},
            {"title": "Bad link", "category": "national", "starts_at": now.isoformat(), "link_url": "javascript:alert(1)"},
            {"title": "Unknown region", "category": "regional", "region": "nowhere", "starts_at": now.isoformat()},
        ]
        for body in bad:
            r = self.client.post("/api/events/", body, content_type="application/json")
            self.assertEqual(r.status_code, 400, (body["title"], r.content))

    # ---- flyer uploads ------------------------------------------------------
    def test_flyer_upload_and_url(self):
        self.client.force_login(self.editor)
        r = self.client.post("/api/events/", {
            "title": "Flyer event", "category": "national", "status": "published",
            "starts_at": (timezone.now() + timedelta(days=30)).isoformat(),
            "flyer": image_file("WEBP", "My Flyer.webp"),
        })
        self.assertEqual(r.status_code, 201, r.content)
        ev = Event.objects.get(title="Flyer event")
        self.assertRegex(ev.flyer.name, r"^flyers/\d{4}/\d{2}/[0-9a-f]{32}\.webp$")
        self.client.logout()
        out = [e for e in self.client.get("/api/events/national/").json()["results"] if e["title"] == "Flyer event"][0]
        self.assertTrue(out["flyer_url"].startswith("http://testserver/media/flyers/"), out["flyer_url"])

    def test_flyer_replace_gets_new_url(self):
        self.client.force_login(self.editor)
        r = self.client.post("/api/events/", {"title": "Replace me", "category": "national",
                                               "starts_at": timezone.now().isoformat(), "flyer": image_file("JPEG", "a.jpg")})
        ev = Event.objects.get(pk=r.json()["id"])
        first = ev.flyer.name
        r = self.client.patch(f"/api/events/{ev.id}/", encode_multipart(BOUNDARY, {"flyer": image_file("PNG", "b.png")}),
                              content_type=MULTIPART_CONTENT)
        self.assertEqual(r.status_code, 200, r.content)
        ev.refresh_from_db()
        self.assertNotEqual(ev.flyer.name, first)
        self.assertTrue(ev.flyer.name.endswith(".png"))

    def test_flyer_rejects_bad_files(self):
        self.client.force_login(self.editor)
        base = {"title": "Bad flyer", "category": "national", "starts_at": timezone.now().isoformat()}
        fake = SimpleUploadedFile("flyer.png", b"not really an image", content_type="image/png")
        self.assertEqual(self.client.post("/api/events/", {**base, "flyer": fake}).status_code, 400)
        self.assertEqual(self.client.post("/api/events/", {**base, "flyer": image_file("GIF", "flyer.gif")}).status_code, 400)
        disguised = image_file("GIF", "flyer.png")  # GIF content with a .png name
        self.assertEqual(self.client.post("/api/events/", {**base, "flyer": disguised}).status_code, 400)
        with self.settings(FLYER_MAX_UPLOAD_BYTES=200):
            big = image_file("PNG", "big.png", size=(400, 400))
            r = self.client.post("/api/events/", {**base, "flyer": big})
            self.assertEqual(r.status_code, 400)
            self.assertIn("too large", str(r.content))
        self.assertFalse(Event.objects.filter(title="Bad flyer").exists())

    def test_anonymous_cannot_upload_flyer(self):
        r = self.client.patch(f"/api/events/{self.nat_up.id}/", encode_multipart(BOUNDARY, {"flyer": image_file()}),
                              content_type=MULTIPART_CONTENT)
        self.assertEqual(r.status_code, 403)

    # ---- CORS ---------------------------------------------------------------
    @override_settings(CORS_ALLOWED_ORIGINS=["https://shadrack213.github.io"])
    def test_cors_only_for_the_website(self):
        ok = self.client.get("/api/events/", HTTP_ORIGIN="https://shadrack213.github.io")
        self.assertEqual(ok.headers.get("Access-Control-Allow-Origin"), "https://shadrack213.github.io")
        other = self.client.get("/api/events/", HTTP_ORIGIN="https://evil.example")
        self.assertIsNone(other.headers.get("Access-Control-Allow-Origin"))
