import logging

from django.db import connection
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .models import ChurchLocation, District, Event, Leader, Ministry, PublishStatus, Region
from .permissions import is_staff
from .serializers import (
    ChurchLocationSerializer, DistrictSerializer, EventSerializer, LeaderSerializer, MinistrySerializer,
    RegionSerializer,
)

logger = logging.getLogger(__name__)


def choice_param(request, name, choices):
    """Read an optional query parameter that must be one of `choices`."""
    value = request.query_params.get(name)
    if value in (None, ""):
        return None
    if value not in choices:
        raise ValidationError({name: f"Must be one of: {', '.join(sorted(choices))}."})
    return value


class EventViewSet(viewsets.ModelViewSet):
    """
    Events. Visitors only ever see published events.

    Filters: ?category=national|headquarters|regional|district  ?region=<slug>  ?district=<slug>
             ?when=upcoming|past  ?page=  ?page_size= (max 200)
    Shortcuts: /api/events/national/  /api/events/headquarters/  /api/events/regional/  /api/events/district/
    """

    serializer_class = EventSerializer
    lookup_value_regex = r"\d+"
    forced_category = None

    def get_queryset(self):
        qs = Event.objects.select_related("region", "district")
        if not is_staff(self.request):
            qs = qs.published()
        if self.action in ("list", "national", "headquarters", "regional", "district"):
            params = self.request.query_params
            category = self.forced_category or choice_param(self.request, "category", set(Event.Category.values))
            if category:
                qs = qs.filter(category=category)
            if params.get("region"):
                qs = qs.filter(region__slug=params["region"])
            if params.get("district"):
                qs = qs.filter(district__slug=params["district"])
            when = choice_param(self.request, "when", {"upcoming", "past"})
            now = timezone.now()
            if when == "upcoming":
                qs = qs.filter(starts_at__gte=now) | qs.filter(ends_at__gte=now)
            elif when == "past":
                qs = qs.filter(starts_at__lt=now).exclude(ends_at__gte=now)
        return qs.order_by("starts_at", "id")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def _category_list(self, request, category):
        self.forced_category = category
        return self.list(request)

    @action(detail=False, methods=["get"])
    def national(self, request):
        return self._category_list(request, Event.Category.NATIONAL)

    @action(detail=False, methods=["get"])
    def headquarters(self, request):
        return self._category_list(request, Event.Category.HEADQUARTERS)

    @action(detail=False, methods=["get"])
    def regional(self, request):
        return self._category_list(request, Event.Category.REGIONAL)

    @action(detail=False, methods=["get"])
    def district(self, request):
        return self._category_list(request, Event.Category.DISTRICT)


class RegionViewSet(viewsets.ModelViewSet):
    """Regions (active ones for visitors). Lookup by slug: /api/regions/ashanti-east/"""

    serializer_class = RegionSerializer
    lookup_field = "slug"

    def get_queryset(self):
        qs = Region.objects.all()
        return qs if is_staff(self.request) else qs.filter(is_active=True)


class DistrictViewSet(viewsets.ModelViewSet):
    """Districts (active ones for visitors). Filter: ?region=<slug>"""

    serializer_class = DistrictSerializer
    lookup_field = "slug"

    def get_queryset(self):
        qs = District.objects.select_related("region")
        if not is_staff(self.request):
            qs = qs.filter(is_active=True)
        if self.request.query_params.get("region"):
            qs = qs.filter(region__slug=self.request.query_params["region"])
        return qs


class ChurchLocationViewSet(viewsets.ModelViewSet):
    """
    Church locations. Visitors see only verified, active locations approved for the website.
    Filters: ?country=GH or ?country=DE,NL   ?kind=...   ?exclude_kind=headquarters
    """

    serializer_class = ChurchLocationSerializer

    def get_queryset(self):
        qs = ChurchLocation.objects.select_related("region", "district")
        if not is_staff(self.request):
            qs = qs.filter(is_verified=True, is_public=True, is_active=True)
        params = self.request.query_params
        if params.get("country"):
            codes = [c.strip().upper() for c in params["country"].split(",") if c.strip()]
            if any(len(c) != 2 or not c.isalpha() for c in codes):
                raise ValidationError({"country": "Use two-letter country codes, e.g. GH or DE,NL."})
            qs = qs.filter(country_code__in=codes)
        kinds = set(ChurchLocation.Kind.values)
        kind = choice_param(self.request, "kind", kinds)
        if kind:
            qs = qs.filter(kind=kind)
        exclude_kind = choice_param(self.request, "exclude_kind", kinds)
        if exclude_kind:
            qs = qs.exclude(kind=exclude_kind)
        return qs


class MinistryViewSet(viewsets.ModelViewSet):
    """Ministries (published ones for visitors). Lookup by slug."""

    serializer_class = MinistrySerializer
    lookup_field = "slug"

    def get_queryset(self):
        qs = Ministry.objects.all()
        return qs if is_staff(self.request) else qs.filter(status=PublishStatus.PUBLISHED)


class LeaderViewSet(viewsets.ModelViewSet):
    """Approved leadership (published records for visitors). Filter: ?scope=headquarters|region|district|zone"""

    serializer_class = LeaderSerializer

    def get_queryset(self):
        qs = Leader.objects.select_related("region", "district")
        if not is_staff(self.request):
            qs = qs.filter(status=PublishStatus.PUBLISHED)
        scope = choice_param(self.request, "scope", set(Leader.Scope.values))
        if scope:
            qs = qs.filter(scope=scope)
        return qs


def database_ok():
    try:
        with connection.cursor() as cursor:
            cursor.execute("select 1")
            cursor.fetchone()
        return True
    except Exception:
        logger.exception("Database health check failed")
        return False


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """GET /api/health/ : confirms the API is up and can reach the database.
    (Normally answered earlier by church.middleware.HealthCheckMiddleware.)"""
    if database_ok():
        return Response({"status": "ok", "database": "ok"})
    return Response({"status": "error", "database": "unavailable"}, status=503)


def api_not_found(request, *args, **kwargs):
    return JsonResponse({"detail": "Not found."}, status=404)


def api_exception_handler(exc, context):
    """DRF's normal error responses, plus a JSON 500 (no internal details) for unexpected errors."""
    response = exception_handler(exc, context)
    if response is None:
        logger.exception("Unhandled API error", exc_info=exc)
        return Response({"detail": "Something went wrong. Please try again later."}, status=500)
    return response
