from django.core.management.base import BaseCommand
from authentication.models import Company

class Command(BaseCommand):
  help = 'Creates default companies'

  def handle(self, *args, **kwargs):
    data = [
      {
        'company_name': 'Acme Inc',
        'company_code': 'ACME',
        'company_type': 'Private',
        'head_office': 'Dhaka',
        'longitude': 90.4125,
        'latitude': 23.8103,
      },
      {
        'company_name': 'Globex Corporation',
        'company_code': 'GLOBEX',
        'company_type': 'Public',
        'head_office': 'Chittagong',
        'longitude': 91.7832,
        'latitude': 22.3569,
      },
      {
        'company_name': 'Initech',
        'company_code': 'INITECH',
        'company_type': 'Private',
        'head_office': 'Sylhet',
        'longitude': 91.8714,
        'latitude': 24.8949,
      },
    ]

    for item in data:
      obj, created = Company.objects.get_or_create(company_code=item['company_code'], defaults=item)
      if created:
        self.stdout.write(self.style.SUCCESS(f"Created company: {obj.company_name}"))
      else:
        self.stdout.write(f"Company already exists: {obj.company_name}")
