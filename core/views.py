import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.db import connection
from django.http import HttpResponseServerError, JsonResponse
from django.shortcuts import redirect, render
from django.template import loader
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from django.views.generic import FormView, TemplateView

from content.models import Category, Content

from .forms import ContactForm
from .ratelimit import ratelimit

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["latest"] = Content.objects.published().select_related("category")[:6]
        context["categories"] = Category.objects.with_published_counts().filter(
            published_count__gt=0
        )
        return context


class AboutView(TemplateView):
    template_name = "about.html"


@method_decorator(ratelimit("contact"), name="dispatch")
class ContactView(FormView):
    template_name = "contact.html"
    form_class = ContactForm
    success_url = reverse_lazy("core:contact")

    def form_valid(self, form):
        if form.is_spam():
            # Pretend it worked so bots learn nothing.
            logger.info("Contact form honeypot triggered; message discarded.")
        else:
            contact = form.save()
            self.notify(contact)
        messages.success(self.request, "Thank you — your message has been sent.")
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)

    @staticmethod
    def notify(contact):
        if not settings.CONTACT_RECIPIENT_EMAIL:
            return
        try:
            send_mail(
                subject=f"[{settings.SITE_NAME}] Contact: {contact.subject}",
                message=f"From: {contact.name} <{contact.email}>\n\n{contact.message}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_RECIPIENT_EMAIL],
            )
        except Exception:
            # The message is already saved; don't fail the request.
            logger.exception("Could not send contact notification email.")


@never_cache
@require_GET
def healthz(request):
    """Liveness/readiness probe: 200 when the app and database respond."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        logger.exception("Health check: database unavailable.")
        return JsonResponse({"status": "error", "database": "unavailable"}, status=503)
    return JsonResponse({"status": "ok", "database": "ok"})


# --- Error handlers -------------------------------------------------------


def bad_request(request, exception=None):
    return render(request, "errors/400.html", status=400)


def permission_denied(request, exception=None):
    return render(request, "errors/403.html", status=403)


def page_not_found(request, exception=None):
    return render(request, "errors/404.html", status=404)


def server_error(request):
    # Rendered without a request context so it works even when the database
    # or a context processor is the thing that failed.
    return HttpResponseServerError(loader.get_template("errors/500.html").render())


def csrf_failure(request, reason=""):
    return render(request, "errors/403_csrf.html", status=403)

