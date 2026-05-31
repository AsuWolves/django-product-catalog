import secrets
import string

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Create (or reset) a temporary local admin superuser with a random password.

    Intended for local/development convenience only — it prints the generated
    password to stdout so you can log into the Django admin without shipping any
    credentials in the repository.
    """

    help = (
        "Create a temporary local admin superuser with a randomly generated "
        "password and print the credentials (local/dev use only)."
    )

    def handle(self, *args, **options):
        username = "admin"
        alphabet = string.ascii_letters + string.digits
        password = "".join(secrets.choice(alphabet) for _ in range(12))

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username)
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} admin user:"))
        self.stdout.write(f"Username: {username}")
        self.stdout.write(f"Password: {password}")
