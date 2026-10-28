"""URL routes: the public API under /api/, and Django Admin at /admin/ once enabled."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("api/", include("church.urls")),
]

# Django Admin is for the later admin phase: switch on with DJANGO_ADMIN_ENABLED=true
if settings.ADMIN_ENABLED:
    admin.site.site_header = "True Faith Church International"
    admin.site.site_title = "TFCI Admin"
    urlpatterns.append(path("admin/", admin.site.urls))

# Uploaded flyers stored on this computer (development only; production uses Supabase Storage)
if settings.DEBUG and not settings.USE_SUPABASE_STORAGE:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
