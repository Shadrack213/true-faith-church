from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import ChurchLocation, District, Event, Leader, Ministry, Region, image_validators


def absolute_media_url(request, url):
    """Uploaded files stored on this server have /media/... URLs; the website runs on
    another address, so give it the full URL. Supabase Storage URLs are already full."""
    if url and url.startswith("/") and request is not None:
        return request.build_absolute_uri(url)
    return url or ""


class ConstraintValidationMixin:
    """Run the model's database constraints (e.g. 'regional events need a region')
    so the API answers 400 with a clear message instead of a database error."""

    def validate(self, attrs):
        attrs = super().validate(attrs)
        instance = self.instance or self.Meta.model()
        for field, value in attrs.items():
            setattr(instance, field, value)
        try:
            instance.validate_constraints()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)
        return attrs


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ["slug", "name", "is_active", "sort_order"]


class DistrictSerializer(serializers.ModelSerializer):
    region = serializers.SlugRelatedField(slug_field="slug", queryset=Region.objects.all(), allow_null=True, required=False)
    region_name = serializers.CharField(source="region.name", read_only=True, default=None)

    class Meta:
        model = District
        fields = ["slug", "name", "region", "region_name", "is_active", "sort_order"]


class EventSerializer(ConstraintValidationMixin, serializers.ModelSerializer):
    region = serializers.SlugRelatedField(slug_field="slug", queryset=Region.objects.all(), allow_null=True, required=False)
    district = serializers.SlugRelatedField(slug_field="slug", queryset=District.objects.all(), allow_null=True, required=False)
    # Field names the website already uses
    region_slug = serializers.CharField(source="region.slug", read_only=True, default=None)
    region_name = serializers.CharField(source="region.name", read_only=True, default=None)
    district_slug = serializers.CharField(source="district.slug", read_only=True, default=None)
    district_name = serializers.CharField(source="district.name", read_only=True, default=None)
    flyer_url = serializers.SerializerMethodField()
    flyer = serializers.ImageField(write_only=True, required=False, allow_null=True, validators=image_validators)

    class Meta:
        model = Event
        fields = [
            "id", "title", "description", "category", "starts_at", "ends_at", "time_zone", "venue",
            "region", "region_slug", "region_name", "district", "district_slug", "district_name",
            "flyer", "flyer_link", "flyer_url", "image_url", "link_url", "status", "published_at",
            "created_at", "updated_at",
        ]
        read_only_fields = ["published_at", "created_at", "updated_at"]
        extra_kwargs = {"flyer_link": {"write_only": True}}

    def get_flyer_url(self, obj):
        return absolute_media_url(self.context.get("request"), obj.flyer_url)


class ChurchLocationSerializer(ConstraintValidationMixin, serializers.ModelSerializer):
    region = serializers.SlugRelatedField(slug_field="slug", queryset=Region.objects.all(), allow_null=True, required=False)
    district = serializers.SlugRelatedField(slug_field="slug", queryset=District.objects.all(), allow_null=True, required=False)
    region_slug = serializers.CharField(source="region.slug", read_only=True, default=None)
    region_name = serializers.CharField(source="region.name", read_only=True, default=None)
    district_slug = serializers.CharField(source="district.slug", read_only=True, default=None)
    district_name = serializers.CharField(source="district.name", read_only=True, default=None)

    class Meta:
        model = ChurchLocation
        fields = [
            "id", "name", "kind", "country_code", "country_name", "region", "region_slug", "region_name",
            "district", "district_slug", "district_name", "locality", "address", "postal_address",
            "phone", "email", "map_url", "is_verified", "is_active", "is_public", "sort_order",
        ]


class MinistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Ministry
        fields = ["slug", "name", "description", "status", "sort_order"]


class LeaderSerializer(serializers.ModelSerializer):
    region = serializers.SlugRelatedField(slug_field="slug", queryset=Region.objects.all(), allow_null=True, required=False)
    district = serializers.SlugRelatedField(slug_field="slug", queryset=District.objects.all(), allow_null=True, required=False)
    photo = serializers.ImageField(write_only=True, required=False, allow_null=True, validators=image_validators)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Leader
        fields = ["id", "full_name", "title", "bio", "photo", "photo_url", "scope", "region", "district", "status", "sort_order"]

    def get_photo_url(self, obj):
        return absolute_media_url(self.context.get("request"), obj.photo.url if obj.photo else "")
