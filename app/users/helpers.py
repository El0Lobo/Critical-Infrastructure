from django.contrib.auth.decorators import user_passes_test


def superuser_required(view):
    return user_passes_test(lambda u: u.is_superuser)(view)
