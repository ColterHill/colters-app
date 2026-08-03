import os
import hashlib
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import json
import logging
from datetime import datetime

from .models import Supplier, POUpload
from .utils import (
    get_airparser_config, 
    get_airparser_upload_url, 
    get_airparser_headers, 
    validate_airparser_setup
)

logger = logging.getLogger(__name__)


class POUploadView(View):
    """Handle purchase order file uploads"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            # Validate request
            if 'file' not in request.FILES:
                return JsonResponse({'error': 'No file provided'}, status=400)
            
            if 'supplier_id' not in request.POST:
                return JsonResponse({'error': 'No supplier specified'}, status=400)
            
            file = request.FILES['file']
            supplier_id = request.POST['supplier_id']
            
            # Validate file type
            if not file.name.lower().endswith('.pdf'):
                return JsonResponse({'error': 'Only PDF files are allowed'}, status=400)
            
            # Validate file size (10MB limit)
            max_size = 10 * 1024 * 1024  # 10MB
            if file.size > max_size:
                return JsonResponse({'error': 'File size exceeds 10MB limit'}, status=400)
            
            # Validate supplier exists and has AirParser inbox ID configured
            try:
                supplier = Supplier.objects.get(id=supplier_id, active=True)
                if not supplier.airparser_inbox_id:
                    return JsonResponse({'error': f'AirParser inbox ID not configured for {supplier.name}'}, status=400)
            except Supplier.DoesNotExist:
                return JsonResponse({'error': 'Invalid supplier selected'}, status=400)
            
            # Calculate file hash for deduplication
            file_content = file.read()
            file_hash = hashlib.sha256(file_content).hexdigest()
            file.seek(0)  # Reset file pointer
            
            # Check for duplicate uploads
            existing_upload = POUpload.objects.filter(
                supplier=supplier,
                file_hash=file_hash,
                status__in=['completed', 'processing']
            ).first()
            
            if existing_upload:
                return JsonResponse({
                    'error': 'This file has already been uploaded and processed',
                    'existing_upload_id': str(existing_upload.id)
                }, status=409)
            
            # Create upload record
            upload = POUpload.objects.create(
                supplier=supplier,
                uploaded_by=request.user if request.user.is_authenticated else None,
                original_filename=file.name,
                file_size=file.size,
                file_hash=file_hash,
                status='uploading'
            )
            
            try:
                # Send to AirParser via API
                api_result = self.send_to_airparser_api(file_content, file.name, supplier, upload)
                
                if api_result['success']:
                    upload.status = 'processing'
                    upload.processed_at = datetime.now()
                    upload.airparser_job_id = api_result.get('document_id')
                    upload.airparser_response = api_result.get('response')
                    upload.save()
                    
                    return JsonResponse({
                        'success': True,
                        'upload_id': str(upload.id),
                        'document_id': api_result.get('document_id'),
                        'message': f'File successfully uploaded to AirParser for {supplier.name}',
                        'inbox_id': supplier.airparser_inbox_id
                    })
                else:
                    upload.status = 'failed'
                    upload.error_message = api_result.get('error', 'Unknown error')
                    upload.save()
                    
                    return JsonResponse({
                        'error': f'AirParser API error: {upload.error_message}'
                    }, status=500)
                    
            except Exception as e:
                upload.status = 'error'
                upload.error_message = str(e)
                upload.save()
                logger.error(f"Error processing upload {upload.id}: {str(e)}")
                raise
                
        except Exception as e:
            logger.error(f"Error in POUploadView: {str(e)}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    def send_to_airparser_api(self, file_content, filename, supplier, upload):
        """Send file to AirParser via API following the official documentation"""
        try:
            # Validate AirParser configuration
            is_valid, error_msg = validate_airparser_setup()
            if not is_valid:
                return {
                    'success': False,
                    'error': error_msg
                }
            
            # Get configuration and prepare URL
            config = get_airparser_config()
            url = get_airparser_upload_url(supplier.airparser_inbox_id)
            headers = get_airparser_headers()
            
            # Prepare metadata payload (optional)
            meta_data = {
                'supplier_id': supplier.id,
                'supplier_name': supplier.name,
                'upload_id': str(upload.id),
                'original_filename': filename,
                'upload_time': upload.created_at.isoformat(),
            }
            
            # Prepare files and data for multipart form upload
            files = {
                'file': (filename, file_content, 'application/pdf')
            }
            
            data = {
                'meta': json.dumps(meta_data)
            }
            
            # Make the API request
            response = requests.post(
                url,
                files=files,
                data=data,
                headers=headers,
                timeout=config['timeout']
            )
            
            if response.status_code in [200, 201]:
                try:
                    result_data = response.json()
                    document_id = result_data if isinstance(result_data, str) else result_data.get('document_id')
                    
                    logger.info(f"Successfully uploaded PDF to AirParser inbox {supplier.airparser_inbox_id} for upload {upload.id}. Document ID: {document_id}")
                    
                    return {
                        'success': True,
                        'document_id': document_id,
                        'response': result_data,
                        'inbox_id': supplier.airparser_inbox_id
                    }
                except json.JSONDecodeError:
                    # Sometimes AirParser returns just the document ID as plain text
                    document_id = response.text.strip()
                    logger.info(f"Successfully uploaded PDF to AirParser inbox {supplier.airparser_inbox_id} for upload {upload.id}. Document ID: {document_id}")
                    
                    return {
                        'success': True,
                        'document_id': document_id,
                        'response': {'document_id': document_id},
                        'inbox_id': supplier.airparser_inbox_id
                    }
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    # Log the full response for debugging
                    logger.error(f"AirParser API error response for upload {upload.id}: {error_data}")
                    error_msg = error_data.get('error', error_data.get('message', error_data.get('statusCode', error_msg)))
                except:
                    error_msg = response.text or error_msg
                    logger.error(f"AirParser API non-JSON error for upload {upload.id}: {error_msg}")
                
                logger.error(f"AirParser API error for upload {upload.id}: Status {response.status_code}, Error: {error_msg}")
                return {
                    'success': False,
                    'error': f"Status {response.status_code}: {error_msg}"
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"AirParser API timeout for upload {upload.id}")
            return {
                'success': False,
                'error': 'AirParser API request timed out'
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"AirParser API network error for upload {upload.id}: {str(e)}")
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error sending to AirParser for upload {upload.id}: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }


@api_view(['GET'])
@permission_classes([AllowAny])
def get_suppliers(request):
    """Get list of active suppliers"""
    try:
        suppliers = Supplier.objects.filter(active=True).values('id', 'name')
        return Response({
            'suppliers': list(suppliers)
        })
    except Exception as e:
        logger.error(f"Error getting suppliers: {str(e)}")
        return Response({'error': 'Internal server error'}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_upload_status(request, upload_id):
    """Get status of a specific upload"""
    try:
        upload = POUpload.objects.get(id=upload_id)
        return Response({
            'upload_id': str(upload.id),
            'status': upload.status,
            'supplier': upload.supplier.name,
            'filename': upload.original_filename,
            'created_at': upload.created_at,
            'processed_at': upload.processed_at,
            'error_message': upload.error_message,
            'extracted_data': upload.extracted_data
        })
    except POUpload.DoesNotExist:
        return Response({'error': 'Upload not found'}, status=404)
    except Exception as e:
        logger.error(f"Error getting upload status: {str(e)}")
        return Response({'error': 'Internal server error'}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_upload_history(request):
    """Get recent upload history"""
    try:
        uploads = POUpload.objects.select_related('supplier').order_by('-created_at')[:50]
        
        upload_data = []
        for upload in uploads:
            upload_data.append({
                'id': str(upload.id),
                'supplier_name': upload.supplier.name,
                'filename': upload.original_filename,
                'status': upload.status,
                'created_at': upload.created_at,
                'processed_at': upload.processed_at,
                'file_size': upload.file_size
            })
        
        return Response({
            'uploads': upload_data
        })
    except Exception as e:
        logger.error(f"Error getting upload history: {str(e)}")
        return Response({'error': 'Internal server error'}, status=500)