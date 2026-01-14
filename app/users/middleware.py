from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.functional import SimpleLazyObject

User = get_user_model()

IMPERSONATE_SESSION_KEY = getattr(settings, "IMPERSONATE_SESSION_KEY", "impersonate_user_id")
IMPERSONATOR_SESSION_KEY = getattr(settings, "IMPERSONATOR_SESSION_KEY", "impersonator_user_id")


class ForcePasswordChangeMiddleware:
    """Redirect authenticated users to onboarding if they must change password or select visibility."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated:
            getattr(user, "profile", None)
            {
                reverse("logout"),
                reverse("password_change"),
                reverse("password_change_done"),
                reverse("login"),
            }

        return self.get_response(request)


def _get_impersonated_user(request):
    """
    Resolve the impersonated user (if any) from the session.
    Return None if not impersonating or if target no longer exists.
    """
    uid = request.session.get(IMPERSONATE_SESSION_KEY)
    if not uid:
        return None
    try:
        return User.objects.get(pk=uid, is_active=True)
    except User.DoesNotExist:
        return None


class ImpersonateMiddleware:
    """
    Must be placed AFTER AuthenticationMiddleware.
    - Exposes request.real_user (the authenticated user who initiated impersonation)
    - If impersonating, sets request.user to the target
    - Exposes request.impersonating (bool) and request.impersonator (User or None)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        real_user = getattr(request, "user", None)
        request.real_user = real_user  # Always keep a handle to the real user

        target_user = _get_impersonated_user(request)
        request.impersonating = target_user is not None
        request.impersonator = real_user if request.impersonating else None

        if target_user:
            # Replace request.user lazily to avoid extra queries
            request.user = SimpleLazyObject(lambda: target_user)

        response = self.get_response(request)
        return response
