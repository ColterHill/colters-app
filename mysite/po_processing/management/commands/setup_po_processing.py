from django.core.management.base import BaseCommand
from po_processing.models import Supplier, AirParserConfig


class Command(BaseCommand):
    help = 'Set up initial data for PO processing system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--airparser-api-key',
            type=str,
            help='AirParser API key to configure',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up PO Processing system...'))
        
        # Create default suppliers
        suppliers_data = [
            {'id': 'acme_corp', 'name': 'ACME Corporation'},
            {'id': 'global_supplies', 'name': 'Global Supplies Inc.'},
            {'id': 'tech_solutions', 'name': 'Tech Solutions Ltd.'},
            {'id': 'industrial_parts', 'name': 'Industrial Parts Co.'},
            {'id': 'office_depot', 'name': 'Office Depot Supply'},
        ]
        
        created_suppliers = 0
        for supplier_data in suppliers_data:
            supplier, created = Supplier.objects.get_or_create(
                id=supplier_data['id'],
                defaults={
                    'name': supplier_data['name'],
                    'active': True
                }
            )
            if created:
                created_suppliers += 1
                self.stdout.write(f"Created supplier: {supplier.name}")
            else:
                self.stdout.write(f"Supplier already exists: {supplier.name}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_suppliers} new suppliers')
        )
        
        # Set up AirParser configuration if API key provided
        api_key = options.get('airparser_api_key')
        if api_key:
            config, created = AirParserConfig.objects.get_or_create(
                active=True,
                defaults={
                    'api_key': api_key,
                    'api_url': 'https://api.airparser.com'
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS('Created AirParser configuration')
                )
            else:
                config.api_key = api_key
                config.save()
                self.stdout.write(
                    self.style.SUCCESS('Updated AirParser configuration')
                )
        else:
            self.stdout.write(
                self.style.WARNING(
                    'No AirParser API key provided. You can set it up later in Django admin.'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS('\nSetup complete! You can now:')
        )
        self.stdout.write('1. Configure AirParser schema IDs for each supplier in Django admin')
        self.stdout.write('2. Visit /po-uploader in your Vue.js frontend to start uploading files')
        self.stdout.write('3. Monitor uploads in Django admin under PO Processing'))
