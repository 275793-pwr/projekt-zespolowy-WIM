from django.core.management.base import BaseCommand

from accounts.models import Role, User


class Command(BaseCommand):
    help = "Creates one student and one corpus admin test account."

    def add_arguments(self, parser):
        parser.add_argument("--password", default="test1234")

    def handle(self, *args, **opts):
        for email, role in [("student@example.com", Role.STUDENT), ("admin@example.com", Role.CORPUS_ADMIN)]:
            user, _ = User.objects.get_or_create(email=email, defaults={"role": role})
            user.role = role
            user.set_password(opts["password"])
            user.save()
            self.stdout.write(f"{email} ({role}) password={opts['password']}")
