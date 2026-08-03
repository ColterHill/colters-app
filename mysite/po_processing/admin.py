from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import Supplier, POUpload


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'active', 'airparser_inbox_id', 'upload_count', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['id', 'name', 'contact_email', 'airparser_inbox_id']
    list_editable = ['active']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'active')
        }),
        ('AirParser Configuration', {
            'fields': ('airparser_inbox_id',),
            'description': 'Each supplier needs their own AirParser inbox ID for document processing via API'
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def upload_count(self, obj):
        count = obj.uploads.count()
        if count > 0:
            url = reverse('admin:po_processing_poupload_changelist') + f'?supplier__id__exact={obj.id}'
            return format_html('<a href="{}">{} uploads</a>', url, count)
        return '0 uploads'
    upload_count.short_description = 'Uploads'


@admin.register(POUpload)
class POUploadAdmin(admin.ModelAdmin):
    list_display = ['id', 'supplier', 'original_filename', 'status', 'file_size_mb', 'uploaded_by', 'created_at']
    list_filter = ['status', 'supplier', 'created_at']
    search_fields = ['id', 'original_filename', 'supplier__name', 'uploaded_by__username']
    readonly_fields = ['id', 'file_hash', 'created_at', 'processed_at', 'airparser_response_formatted', 'extracted_data_formatted']
    
    fieldsets = (
        ('Upload Information', {
            'fields': ('id', 'supplier', 'uploaded_by', 'original_filename', 'file_size', 'file_hash')
        }),
        ('Processing Status', {
            'fields': ('status', 'airparser_job_id', 'error_message')
        }),
        ('AirParser Response', {
            'fields': ('airparser_response_formatted', 'extracted_data_formatted'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at')
        })
    )
    
    def file_size_mb(self, obj):
        if obj.file_size:
            mb = obj.file_size / (1024 * 1024)
            return f"{mb:.2f} MB"
        return "Unknown"
    file_size_mb.short_description = 'File Size'
    
    def airparser_response_formatted(self, obj):
        if obj.airparser_response:
            formatted = json.dumps(obj.airparser_response, indent=2)
            return format_html('<pre style="white-space: pre-wrap;">{}</pre>', formatted)
        return "No response data"
    airparser_response_formatted.short_description = 'AirParser Response'
    
    def extracted_data_formatted(self, obj):
        if obj.extracted_data:
            formatted = json.dumps(obj.extracted_data, indent=2)
            return format_html('<pre style="white-space: pre-wrap;">{}</pre>', formatted)
        return "No extracted data"
    extracted_data_formatted.short_description = 'Extracted Data'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('supplier', 'uploaded_by')



