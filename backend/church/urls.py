"""
API routes (all under /api/):

  GET /api/                         list of endpoints
  GET /api/health/                  API + database check
  GET /api/events/                  ?category= ?region= ?district= ?when=upcoming|past
  GET /api/events/national/         national events
  GET /api/events/headquarters/     headquarters events
  GET /api/events/regional/         ?region=<slug>
  GET /api/events/district/         ?district=<slug>
  GET /api/events/<id>/
  GET /api/regions/   /api/regions/<slug>/
  GET /api/districts/ /api/districts/<slug>/       ?region=<slug>
  GET /api/church-locations/        ?country=GH ?kind= ?exclude_kind=
  GET /api/ministries/ /api/ministries/<slug>/
  GET /api/leadership/              ?scope=

Writes (POST/PUT/PATCH/DELETE) need a signed-in staff account with model permissions.
"""
from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("events", views.EventViewSet, basename="event")
router.register("regions", views.RegionViewSet, basename="region")
router.register("districts", views.DistrictViewSet, basename="district")
router.register("church-locations", views.ChurchLocationViewSet, basename="church-location")
router.register("ministries", views.MinistryViewSet, basename="ministry")
router.register("leadership", views.LeaderViewSet, basename="leader")

urlpatterns = [
    path("health/", views.health, name="health"),
    path("", include(router.urls)),
    re_path(r"^.*$", views.api_not_found),
]
