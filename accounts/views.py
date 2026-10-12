from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import CreateView, TemplateView, UpdateView

from core.ratelimit import ratelimit

from .forms import ProfileForm, RegistrationForm


@method_decorator(sensitive_post_parameters("password1", "password2"), name="dispatch")
@method_decorator(ratelimit("register"), name="dispatch")
class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("accounts:profile")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("accounts:profile")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(self.request, "Welcome! Your account has been created.")
        return redirect(self.success_url)


@method_decorator(ratelimit("login"), name="dispatch")
class LoginView(auth_views.LoginView):
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "You are now signed in.")
        return response


class LogoutView(auth_views.LogoutView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.info(request, "You have been signed out.")
        return response


@method_decorator(ratelimit("password_reset"), name="dispatch")
class PasswordResetView(auth_views.PasswordResetView):
    def form_valid(self, form):
        # Name the site in the email rather than showing the bare host name.
        self.extra_email_context = {"site_name": settings.SITE_NAME}
        return super().form_valid(form)


class PasswordChangeView(SuccessMessageMixin, auth_views.PasswordChangeView):
    success_url = reverse_lazy("accounts:profile")
    success_message = "Your password has been changed."


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"


class ProfileEditView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = ProfileForm
    template_name = "accounts/profile_edit.html"
    success_url = reverse_lazy("accounts:profile")
    success_message = "Your profile has been updated."

    def get_object(self, queryset=None):
        return self.request.user
