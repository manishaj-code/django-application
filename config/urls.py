from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from accounts.urls import auth_patterns
from core import views as core_views
from core.ratelimit import ratelimit

admin.site.site_header = f"{settings.SITE_NAME} administration"
admin.site.site_title = f"{settings.SITE_NAME} admin"
admin.site.index_title = "Content management"
# Throttle admin sign-in attempts with the same limit as the public login.
admin.site.login = ratelimit("login")(admin.site.login)

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("accounts/", include(auth_patterns)),
    path("accounts/", include("accounts.urls")),
    path("content/", include("content.urls")),
    path("healthz/", core_views.healthz, name="healthz"),
    path("", include("core.urls")),
]

if settings.DEBUG:
    # Development only. In production media is served by the web server or
    # object storage (see docs/DEPLOYMENT.md).
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif settings.SERVE_MEDIA:
    # Single-service hosts without nginx (e.g. Render). Uploads are validated
    # images only; SecurityHeadersMiddleware adds CSP and nosniff applies.
    urlpatterns += [
        re_path(
            r"^%s(?P<path>.*)$" % settings.MEDIA_URL.lstrip("/"),
            serve,
            {"document_root": settings.MEDIA_ROOT},
        )
    ]

handler400 = "core.views.bad_request"
handler403 = "core.views.permission_denied"
handler404 = "core.views.page_not_found"
handler500 = "core.views.server_error"
