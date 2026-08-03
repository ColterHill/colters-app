#!/usr/bin/env python3
"""
Initialization script for the Purchase Order Processing System

This script helps set up the PO processing system with sample data.
Run this after creating migrations and migrating the database.

Usage:
    python init_po_system.py [--airparser-api-key YOUR_API_KEY]
"""

import os
import sys
import django

# Add the mysite directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'mysite'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from po_processing.models import Supplier


def create_sample_suppliers():
    """Create sample supplier data"""
    suppliers_data = [
        {
            'id': 'test_supplier', 
            'name': 'Test Supplier (AirParser Configured)', 
            'contact_email': 'test@supplier.com',
            'airparser_inbox_id': '68bf19bf8fb7546120660a49'
        },
        {'id': 'acme_corp', 'name': 'ACME Corporation', 'contact_email': 'orders@acme.com'},
        {'id': 'global_supplies', 'name': 'Global Supplies Inc.', 'contact_email': 'po@globalsupplies.com'},
        {'id': 'tech_solutions', 'name': 'Tech Solutions Ltd.', 'contact_email': 'purchasing@techsolutions.com'},
        {'id': 'industrial_parts', 'name': 'Industrial Parts Co.', 'contact_email': 'orders@industrialparts.com'},
        {'id': 'office_depot', 'name': 'Office Depot Supply', 'contact_email': 'business@officedepot.com'},
    ]
    
    created_count = 0
    for supplier_data in suppliers_data:
        supplier, created = Supplier.objects.get_or_create(
            id=supplier_data['id'],
            defaults=supplier_data
        )
        if created:
            created_count += 1
            print(f"✓ Created supplier: {supplier.name}")
        else:
            print(f"- Supplier already exists: {supplier.name}")
    
    return created_count


def setup_airparser_config(api_key=None):
    """Display AirParser configuration instructions"""
    print("🔧 AirParser API Setup:")
    print("  Each supplier needs their own AirParser inbox ID")
    print("  Test supplier is pre-configured with inbox ID: 68bf19bf8fb7546120660a49")
    print("  ")
    if api_key:
        print(f"  ⚠ API Key provided: {api_key[:8]}...")
        print("  Please add this to po_processing/utils.py:")
        print(f"  Change 'YOUR_API_KEY_HERE' to '{api_key}'")
        return True
    else:
        print("  To configure your API key:")
        print("  1. Edit mysite/po_processing/utils.py")
        print("  2. Replace 'YOUR_API_KEY_HERE' with your actual AirParser API key")
        print("  3. Or run: python init_po_system.py --airparser-api-key=YOUR_KEY")
        return False


def main():
    print("🚀 Initializing Purchase Order Processing System")
    print("=" * 50)
    
    # Check for API key argument
    api_key = None
    if len(sys.argv) > 1 and sys.argv[1].startswith('--airparser-api-key'):
        if '=' in sys.argv[1]:
            api_key = sys.argv[1].split('=', 1)[1]
        elif len(sys.argv) > 2:
            api_key = sys.argv[2]
    
    # Create suppliers
    print("\n📋 Setting up suppliers...")
    created_suppliers = create_sample_suppliers()
    print(f"✓ Setup complete: {created_suppliers} new suppliers created")
    
    # Setup AirParser configuration
    print("\n🔧 AirParser API Configuration...")
    api_configured = setup_airparser_config(api_key)
    
    # Print summary
    print("\n" + "=" * 50)
    print("🎉 Setup Complete!")
    print("\nNext steps:")
    print("1. Start your Django server: python mysite/manage.py runserver")
    print("2. Start your Vue.js frontend: cd mysite/cloudv2 && npm run serve")
    print("3. Visit http://localhost:8080/po-uploader to test file uploads")
    print("4. Access Django admin at http://localhost:8000/admin/")
    print("5. Select 'Test Supplier (AirParser Configured)' to test with your AirParser inbox")
    
    if not api_configured:
        print("\n⚠ Remember to add your AirParser API key to po_processing/utils.py!")
    
    print("\n📚 Additional configuration:")
    print("- Add AirParser inbox IDs for other suppliers in Django admin")
    print("- Configure supplier contact information and notes")
    print("- Monitor uploads and processing in the admin interface")
    print("- Check your AirParser dashboard for processed documents")


if __name__ == '__main__':
    main()
