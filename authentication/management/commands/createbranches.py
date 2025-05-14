from django.core.management.base import BaseCommand
from authentication.models import Branch, Company

class Command(BaseCommand):
  help = 'Creates default branches'

  def handle(self, *args, **kwargs):
    try:
      company1 = Company.objects.get(company_code='ACME')
      company2 = Company.objects.get(company_code='GLOBEX')
      company3 = Company.objects.get(company_code='INITECH')
    except Company.DoesNotExist:
      self.stderr.write("Company with code 'ACME' not found.")
      return

    data = [
      {
        'branch_code': 'ACME-DHK',
        'company': company1,
        'branch_name': 'Dhaka Branch',
        'address': 'Banani, Dhaka',
        'longitude': 90.4120,
        'latitude': 23.8100,
      },
      {
        'branch_code': 'GLOBEX-CTG',
        'company': company2,
        'branch_name': 'Chittagong Branch',
        'address': 'Chawkbazar, Chittagong',
        'longitude': 91.7832,
        'latitude': 22.3569,
      },
      {
        'branch_code': 'INITECH-SYL',
        'company': company3,
        'branch_name': 'Sylhet Branch',
        'address': 'Zindabazar, Sylhet',
        'longitude': 91.8714,
        'latitude': 24.8949,
      },
      {
        'branch_code': 'INITECH-CTG',
        'company': company3,
        'branch_name': 'Chittagong Branch',
        'address': 'Chawkbazar, Chittagong',
        'longitude': 91.7832,
        'latitude': 22.3569,
      },
      {
        'branch_code': 'INITECH-DHK',
        'company': company3,
        'branch_name': 'Dhaka Branch',
        'address': 'Banani, Dhaka',
        'longitude': 90.4120,
        'latitude': 23.8100,
      }
    ]

    for item in data:
      obj, created = Branch.objects.get_or_create(branch_code=item['branch_code'], defaults=item)
      if created:
        self.stdout.write(self.style.SUCCESS(f"Created branch: {obj.branch_name}"))
      else:
        self.stdout.write(f"Branch already exists: {obj.branch_name}")
