"""Grant the admin role to a user by email.

This is the only way to assign the ``admin`` role (spec 04, Requirement 2.5); it cannot be
done through the API. Usage: ``python manage.py set_admin <email>``.
"""

from django.core.management.base import BaseCommand, CommandError

from api.repositories import users as users_repo


class Command(BaseCommand):
    help = "Grant the admin role to the user with the given email."

    def add_arguments(self, parser):
        parser.add_argument("email", help="Email of the user to promote to admin.")

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        user = users_repo.set_admin_by_email(email)
        if user is None:
            raise CommandError(f"No user found with email {email!r}.")
        self.stdout.write(self.style.SUCCESS(f"{email} is now an admin."))
