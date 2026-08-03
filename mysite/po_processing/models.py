from django.db import models
from django.contrib.auth.models import User
import uuid

class Supplier(models.Model):
    """Model to store supplier information and their AirParser API configuration"""
    id = models.CharField(max_length=50, primary_key=True)  # e.g., 'acme_corp'
    name = models.CharField(max_length=200)  # e.g., 'ACME Corporation'
    airparser_inbox_id = models.CharField(max_length=100, blank=True, null=True, help_text="AirParser inbox ID (e.g., 68bf19bf8fb7546120660a49)")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional configuration fields
    contact_email = models.EmailField(blank=True, null=True, help_text="Supplier's contact email")
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class POUpload(models.Model):
    """Model to track purchase order uploads and their processing status"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Upload'),
        ('uploading', 'Uploading to AirParser'),
        ('processing', 'Processing by AirParser'),
        ('completed', 'Successfully Processed'),
        ('failed', 'Processing Failed'),
        ('error', 'Upload Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='uploads')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # File information
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()  # Size in bytes
    file_hash = models.CharField(max_length=64, blank=True, null=True)  # SHA-256 hash for deduplication
    
    # Processing status and results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    airparser_job_id = models.CharField(max_length=100, blank=True, null=True)
    airparser_response = models.JSONField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Extracted data (populated after successful processing)
    extracted_data = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.supplier.name} - {self.original_filename} ({self.status})"

    class Meta:
        ordering = ['-created_at']



