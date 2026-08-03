"""
AirParser configuration and utility functions for PO processing
"""

# AirParser API Configuration
AIRPARSER_CONFIG = {
    'api_key': 'yh91crkqf41v3t17ptaeqto8i7v4pmuape16t0swkup03ebw',  # Replace with your actual AirParser API key
    'api_url': 'https://api.airparser.com',
    'timeout': 30,  # Request timeout in seconds
    'max_file_size': 20 * 1024 * 1024,  # 20MB as per AirParser docs
}


def get_airparser_config():
    """
    Get AirParser configuration
    
    Returns:
        dict: AirParser configuration settings
    """
    return AIRPARSER_CONFIG.copy()


def is_airparser_configured():
    """
    Check if AirParser is properly configured
    
    Returns:
        bool: True if API key is set, False otherwise
    """
    return (
        AIRPARSER_CONFIG['api_key'] and 
        AIRPARSER_CONFIG['api_key'] != 'YOUR_API_KEY_HERE'
    )


def get_airparser_upload_url(inbox_id):
    """
    Get the AirParser upload URL for a specific inbox
    
    Args:
        inbox_id (str): AirParser inbox ID
        
    Returns:
        str: Complete upload URL
    """
    base_url = AIRPARSER_CONFIG['api_url'].rstrip('/')
    return f"{base_url}/inboxes/{inbox_id}/upload"


def get_airparser_headers():
    """
    Get the required headers for AirParser API requests
    
    Returns:
        dict: Headers dictionary with API key
    """
    return {
        'X-API-Key': AIRPARSER_CONFIG['api_key']
    }


def validate_airparser_setup():
    """
    Validate AirParser configuration
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not is_airparser_configured():
        return False, "AirParser API key not configured in po_processing/utils.py"
    
    if not AIRPARSER_CONFIG['api_url']:
        return False, "AirParser API URL not configured"
    
    return True, None
