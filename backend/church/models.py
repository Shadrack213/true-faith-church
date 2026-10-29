"""
Database models for True Faith Church International.

Public visibility rules (enforced in the API, see church/views.py):
  Region / District    is_active
  Event                status = published
  ChurchLocation       is_verified and is_public
  Ministry / Leader    status = published
"""
from django.conf import settings
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .validators import ALLOWED_EXTENSIONS, UniqueUploadPath, validate_image_upload

slug_validator = RegexValidator(r"^[a-z0-9]+(-[a-z0-9]+)*$", "Use lowercase letters, numbers and single dashes.")
safe_link_validator = RegexValidator(r"^(https://|assets/)", "Use an https:// link or a file in the website's assets/ folder.")
image_validators = [FileExtensionValidator(ALLOWED_EXTENSIONS), validate_image_upload]


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Region(TimeStamped):
    """One of the church's 20 regions. The slug matches the page events-<slug>.html."""

    slug = models.SlugField(max_length=80, unique=True, validators=[slug_validator])
    name = models.CharField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class District(TimeStamped):
    """One of the church's 80 districts. Leave region empty until the link is verified."""

    slug = models.SlugField(max_length=80, unique=True, validators=[slug_validator])
    name = models.CharField(max_length=120, unique=True)
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.SET_NULL, related_name="districts",
                               help_text="Only set once the region is verified.")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class PublishStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class EventQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=PublishStatus.PUBLISHED)


class Event(TimeStamped):
    class Category(models.TextChoices):
        NATIONAL = "national", "National"
        HEADQUARTERS = "headquarters", "Headquarters"
        REGIONAL = "regional", "Regional"
        DISTRICT = "district", "District"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=12, choices=Category.choices)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    time_zone = models.CharField(max_length=50, default="Africa/Accra", help_text="Used to show the local date and time.")
    venue = models.CharField(max_length=200, blank=True)
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.PROTECT, related_name="events")
    district = models.ForeignKey(District, null=True, blank=True, on_delete=models.PROTECT, related_name="events")
    # Flyer: an uploaded image (stored in Supabase Storage) or, for older flyers, a link
    flyer = models.ImageField(upload_to=UniqueUploadPath("flyers"), blank=True, validators=image_validators,
                              help_text="JPEG, PNG or WebP, up to 5 MB.")
    flyer_link = models.CharField(max_length=500, blank=True, validators=[safe_link_validator],
                                  help_text="Only if the flyer is not uploaded above (https:// or assets/...).")
    image_url = models.CharField(max_length=500, blank=True, validators=[safe_link_validator],
                                 help_text="Optional event photo.")
    link_url = models.URLField(max_length=500, blank=True, validators=[RegexValidator(r"^https://", "Use an https:// link.")],
                               help_text="Optional link, e.g. a photo gallery.")
    status = models.CharField(max_length=10, choices=PublishStatus.choices, default=PublishStatus.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True, editable=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   editable=False, related_name="+")

    objects = EventQuerySet.as_manager()

    class Meta:
        ordering = ["starts_at"]
        indexes = [
            models.Index(fields=["status", "category", "starts_at"], name="event_public_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                name="event_category_target",
                condition=(
                    Q(category__in=["national", "headquarters"], region__isnull=True, district__isnull=True)
                    | Q(category="regional", region__isnull=False, district__isnull=True)
                    | Q(category="district", district__isnull=False)
                ),
                violation_error_message="National and Headquarters events have no region or district; regional events need a "
                                        "region; district events need a district.",
            ),
            models.CheckConstraint(
                name="event_end_after_start",
                condition=Q(ends_at__isnull=True) | Q(ends_at__gte=models.F("starts_at")),
                violation_error_message="The end time cannot be before the start time.",
            ),
            models.UniqueConstraint(fields=["title", "starts_at", "category"], name="event_unique_title_start"),
        ]

    def __str__(self):
        return f"{self.title} ({self.starts_at:%d %b %Y})"

    @property
    def flyer_url(self):
        """The URL the website should display for the flyer ('' if none)."""
        if self.flyer:
            return self.flyer.url
        return self.flyer_link

    def save(self, *args, **kwargs):
        if self.status == PublishStatus.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        elif self.status == PublishStatus.DRAFT:
            self.published_at = None
        super().save(*args, **kwargs)


class ChurchLocation(TimeStamped):
    class Kind(models.TextChoices):
        HEADQUARTERS = "headquarters", "Headquarters"
        GHANA_BRANCH = "ghana_branch", "Ghana branch"
        INTERNATIONAL_BRANCH = "international_branch", "International branch"

    name = models.CharField(max_length=160)
    kind = models.CharField(max_length=24, choices=Kind.choices)
    country_code = models.CharField(max_length=2, validators=[RegexValidator(r"^[A-Z]{2}$", "Two capital letters, e.g. GH.")],
                                    help_text="ISO code: GH, CI, TG, US, GB, CA, AE, DE, NL ...")
    country_name = models.CharField(max_length=80)
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.SET_NULL, related_name="locations")
    district = models.ForeignKey(District, null=True, blank=True, on_delete=models.SET_NULL, related_name="locations")
    locality = models.CharField("city or locality", max_length=120, blank=True)
    address = models.CharField("verified address", max_length=300, blank=True,
                               help_text="Enter only an address the church has confirmed.")
    postal_address = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    map_url = models.URLField("map link", max_length=500, blank=True,
                              validators=[RegexValidator(r"^https://", "Use an https:// link.")],
                              help_text="Optional Google Maps link to the branch.")
    is_verified = models.BooleanField(default=False, help_text="Confirmed by the church as a real branch.")
    is_active = models.BooleanField(default=True, help_text="The branch is currently operating.")
    is_public = models.BooleanField(default=False, help_text="Approved to show on the website.")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        indexes = [models.Index(fields=["country_code", "sort_order"], name="location_country_idx")]
        constraints = [
            models.UniqueConstraint(fields=["country_code", "name"], name="location_unique_name_per_country"),
            models.CheckConstraint(name="location_public_needs_verified", condition=Q(is_public=False) | Q(is_verified=True),
                                   violation_error_message="Only verified locations can be shown publicly."),
            models.CheckConstraint(name="location_kind_country",
                                   condition=(Q(kind="international_branch") & ~Q(country_code="GH"))
                                   | Q(kind__in=["headquarters", "ghana_branch"], country_code="GH"),
                                   violation_error_message="Headquarters and Ghana branches are in Ghana (GH); "
                                                           "international branches are outside Ghana."),
        ]

    def __str__(self):
        return f"{self.name} ({self.country_code})"


class Ministry(TimeStamped):
    slug = models.SlugField(max_length=80, unique=True, validators=[slug_validator])
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=PublishStatus.choices, default=PublishStatus.DRAFT)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "ministries"

    def __str__(self):
        return self.name


class Leader(TimeStamped):
    """Approved leadership records only. Nothing is shown until published."""

    class Scope(models.TextChoices):
        HEADQUARTERS = "headquarters", "Headquarters"
        REGION = "region", "Region"
        DISTRICT = "district", "District"
        ZONE = "zone", "Zone"

    full_name = models.CharField(max_length=160)
    title = models.CharField(max_length=120)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to=UniqueUploadPath("leaders"), blank=True, validators=image_validators)
    scope = models.CharField(max_length=12, choices=Scope.choices)
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.SET_NULL, related_name="leaders")
    district = models.ForeignKey(District, null=True, blank=True, on_delete=models.SET_NULL, related_name="leaders")
    status = models.CharField(max_length=10, choices=PublishStatus.choices, default=PublishStatus.DRAFT)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["scope", "sort_order", "full_name"]
        constraints = [
            models.UniqueConstraint(fields=["full_name", "title", "scope"], name="leader_unique_name_title_scope"),
        ]

    def __str__(self):
        return f"{self.full_name}, {self.title}"
