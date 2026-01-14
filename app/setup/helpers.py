from .models import SiteSettings, VisibilityRule


def get_settings():
    return SiteSettings.get_solo()


def is_allowed(user, key: str) -> bool:
    try:
        rule = VisibilityRule.objects.get(key=key)
    except VisibilityRule.DoesNotExist:
        if user.is_superuser:
            return True
        if key.startswith("cms.users"):
            return False  # sensitive user data is hidden unless explicitly allowed
        return True  # no rule means visible

    if not rule.is_enabled:
        return False

    if user.is_superuser:
        return True
    if not rule.allowed_groups.exists():
        return False
    return rule.allowed_groups.filter(id__in=user.groups.values_list("id", flat=True)).exists()
