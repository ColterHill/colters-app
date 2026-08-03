#!/usr/bin/env python3
"""
Simple script to update the AirParser API key in utils.py

Usage:
    python update_api_key.py YOUR_API_KEY
"""

import sys
import os

def update_api_key(api_key):
    """Update the API key in po_processing/utils.py"""
    utils_path = os.path.join(os.path.dirname(__file__), 'mysite', 'po_processing', 'utils.py')
    
    if not os.path.exists(utils_path):
        print(f"❌ Error: {utils_path} not found")
        return False
    
    try:
        # Read the current file
        with open(utils_path, 'r') as f:
            content = f.read()
        
        # Replace the API key
        old_line = "'api_key': 'YOUR_API_KEY_HERE',"
        new_line = f"'api_key': '{api_key}',"
        
        if old_line in content:
            content = content.replace(old_line, new_line)
            
            # Write the updated file
            with open(utils_path, 'w') as f:
                f.write(content)
            
            print(f"✅ Successfully updated API key in {utils_path}")
            print(f"   New key: {api_key[:8]}...{api_key[-4:]}")
            return True
        else:
            print("⚠️  Warning: Could not find 'YOUR_API_KEY_HERE' in utils.py")
            print("   Please manually update the API key in po_processing/utils.py")
            return False
            
    except Exception as e:
        print(f"❌ Error updating API key: {str(e)}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python update_api_key.py YOUR_API_KEY")
        print("Example: python update_api_key.py sk-123456789abcdef")
        sys.exit(1)
    
    api_key = sys.argv[1]
    
    if len(api_key) < 10:
        print("❌ Error: API key seems too short. Please check your key.")
        sys.exit(1)
    
    print("🔧 Updating AirParser API key...")
    success = update_api_key(api_key)
    
    if success:
        print("\n🎉 Setup complete! You can now:")
        print("1. Start Django: cd mysite && python manage.py runserver")
        print("2. Start Vue.js: cd mysite/cloudv2 && npm run serve")
        print("3. Test uploads at http://localhost:8080/po-uploader")
    else:
        print("\n❌ Failed to update API key. Please manually edit po_processing/utils.py")

if __name__ == '__main__':
    main()
