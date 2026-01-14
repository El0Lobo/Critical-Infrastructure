from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a DEV admin user quickly (development/test environments only)."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="admin")
        parser.add_argument("--email", default="admin@example.com")
        parser.add_argument("--password", default="admin123")

    def handle(self, *args, **opts):
        if settings.ENV not in ("development", "test"):
            self.stderr.write(
                f"Refusing to run in {settings.ENV} environment. "
                "Set DJANGO_ENV=development to enable."
            )
            return
        User = get_user_model()
        user = User.objects.filter(username=opts["username"]).first()
        if user:
            user.is_superuser = True
            user.is_staff = True
            user.set_password(opts["password"])
            user.save(update_fields=["is_superuser", "is_staff", "password"])
            u = user
            self.stdout.write("Updated existing admin user.")
        else:
            u = User.objects.create_superuser(opts["username"], "", opts["password"])
            self.stdout.write(f"Created superuser {u.username}")

        if opts.get("email"):
            profile = getattr(u, "profile", None)
            if profile:
                profile.email = opts["email"]
                profile.save(update_fields=["email"])
