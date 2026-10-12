from django.conf import settings


def site(request):
    """Values every template may use."""
    return {
        "SITE_NAME": settings.SITE_NAME,
        "ADMIN_URL": "/" + settings.ADMIN_URL,
    }
