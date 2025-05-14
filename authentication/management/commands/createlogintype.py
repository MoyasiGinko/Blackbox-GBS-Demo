from django.core.management.base import BaseCommand
from authentication.models import LoginType

class Command(BaseCommand):
  help = 'Creates default login types'

  def handle(self, *args, **kwargs):
    types = ['fmc', 'erp', 'vendor', 'customer']

    for login_type in types:
      obj, created = LoginType.objects.get_or_create(login_type=login_type)
      if created:
        self.stdout.write(self.style.SUCCESS(f"Created login type: {login_type}"))
      else:
        self.stdout.write(f"Login type already exists: {login_type}")
