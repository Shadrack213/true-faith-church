"""
Django Admin set-up for the later admin phase.
/admin/ is only switched on when DJANGO_ADMIN_ENABLED=true (see config/urls.py).
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import ChurchLocation, District, Event, Leader, Ministry, Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "sort_order"]
    list_editable = ["is_active", "sort_order"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "region", "is_active", "sort_order"]
    list_filter = ["region", "is_active"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "starts_at", "region", "district", "status", "flyer_preview"]
    list_filter = ["status", "category", "region", "district"]
    search_fields = ["title", "venue", "description"]
    date_hierarchy = "starts_at"
    readonly_fields = ["flyer_preview", "published_at", "created_by", "created_at", "updated_at"]
    autocomplete_fields = ["region", "district"]
    fieldsets = [
        (None, {"fields": ["title", "description", "category", "status"]}),
        ("When and where", {"fields": ["starts_at", "ends_at", "time_zone", "venue", "region", "district"]}),
        ("Flyer and links", {"fields": ["flyer", "flyer_preview", "flyer_link", "image_url", "link_url"]}),
        ("Record", {"fields": ["published_at", "created_by", "created_at", "updated_at"]}),
    ]

    @admin.display(description="Flyer")
    def flyer_preview(self, obj):
        url = obj.flyer_url
        return format_html('<img src="{}" style="max-height:120px">', url) if url and url.startswith("http") else (url or "-")

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ChurchLocation)
class ChurchLocationAdmin(admin.ModelAdmin):
    list_display = ["name", "kind", "country_code", "locality", "is_verified", "is_active", "is_public"]
    list_filter = ["kind", "country_code", "is_verified", "is_active", "is_public"]
    search_fields = ["name", "locality", "address"]
    autocomplete_fields = ["region", "district"]


@admin.register(Ministry)
class MinistryAdmin(admin.ModelAdmin):
    list_display = ["name", "status", "sort_order"]
    list_filter = ["status"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Leader)
class LeaderAdmin(admin.ModelAdmin):
    list_display = ["full_name", "title", "scope", "region", "district", "status"]
    list_filter = ["scope", "status"]
    search_fields = ["full_name", "title"]
    autocomplete_fields = ["region", "district"]
