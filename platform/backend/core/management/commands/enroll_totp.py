from getpass import getpass

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django_otp.plugins.otp_totp.models import TOTPDevice


class Command(BaseCommand):
    help = "Enroll an existing administrator locally. Treat the displayed URI as a credential."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **options):
        user = User.objects.get(username=options["username"])
        if not user.check_password(getpass("Current password: ")):
            raise CommandError("Authentication failed")
        if TOTPDevice.objects.filter(user=user, confirmed=True).exists():
            raise CommandError("A confirmed device already exists")
        device = TOTPDevice.objects.create(user=user, name="Authenticator", confirmed=False)
        self.stdout.write(
            "Add this URI to your authenticator in a private terminal (do not share):"
        )
        self.stdout.write(device.config_url)
        token = getpass("Authenticator code: ")
        if not device.verify_token(token):
            device.delete()
            raise CommandError("Code verification failed; device removed")
        device.confirmed = True
        device.save(update_fields=["confirmed"])
        self.stdout.write("2FA enrollment complete")
