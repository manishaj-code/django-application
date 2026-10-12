from django.conf import settings


class SecurityHeadersMiddleware:
    """
    Adds Content-Security-Policy and Permissions-Policy headers.

    The admin is excluded from CSP because Django's admin is not designed for
    a strict policy. When DEBUG is on, error pages are skipped too, because
    Django's technical error pages rely on inline styles and scripts.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_prefix = "/" + settings.ADMIN_URL

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault("Permissions-Policy", settings.PERMISSIONS_POLICY)
        policy = settings.CONTENT_SECURITY_POLICY
        if (
            policy
            and not request.path.startswith(self.admin_prefix)
            and not (settings.DEBUG and response.status_code >= 400)
        ):
            response.setdefault("Content-Security-Policy", policy)
        return response
