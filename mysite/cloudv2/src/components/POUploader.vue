<template>
  <div class="po-uploader-container">
    <div class="upload-card">
      <h2 class="upload-title">Purchase Order Uploader</h2>
      <p class="upload-subtitle">Upload supplier purchase orders for automated processing</p>
      
      <!-- Supplier Selection -->
      <div class="form-group">
        <label for="supplier-select" class="form-label">Select Supplier:</label>
        <select 
          id="supplier-select"
          v-model="selectedSupplier" 
          class="form-select"
          :disabled="uploading"
        >
          <option value="">Choose a supplier...</option>
          <option 
            v-for="supplier in suppliers" 
            :key="supplier.id" 
            :value="supplier.id"
          >
            {{ supplier.name }}
          </option>
        </select>
      </div>

      <!-- File Upload Area -->
      <div class="file-upload-section">
        <div 
          class="file-drop-zone"
          :class="{ 
            'drag-over': dragOver, 
            'has-file': selectedFile,
            'disabled': uploading 
          }"
          @drop="handleDrop"
          @dragover="handleDragOver"
          @dragleave="handleDragLeave"
          @click="triggerFileInput"
        >
          <input
            ref="fileInput"
            type="file"
            accept=".pdf,application/pdf"
            @change="handleFileSelect"
            class="file-input-hidden"
            :disabled="uploading"
          />
          
          <div v-if="!selectedFile" class="drop-zone-content">
            <i class="pi pi-cloud-upload upload-icon"></i>
            <p class="upload-text">
              <strong>Click to upload</strong> or drag and drop
            </p>
            <p class="upload-hint">PDF files only (max 10MB)</p>
          </div>
          
          <div v-else class="file-selected">
            <i class="pi pi-file-pdf file-icon"></i>
            <div class="file-info">
              <p class="file-name">{{ selectedFile.name }}</p>
              <p class="file-size">{{ formatFileSize(selectedFile.size) }}</p>
            </div>
            <button 
              v-if="!uploading"
              @click.stop="removeFile" 
              class="remove-file-btn"
              type="button"
            >
              <i class="pi pi-times"></i>
            </button>
          </div>
        </div>
      </div>

      <!-- Upload Progress -->
      <div v-if="uploading" class="upload-progress">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
        </div>
        <p class="progress-text">{{ uploadStatusText }}</p>
      </div>

      <!-- Error Message -->
      <div v-if="errorMessage" class="error-message">
        <i class="pi pi-exclamation-triangle"></i>
        {{ errorMessage }}
      </div>

      <!-- Success Message -->
      <div v-if="successMessage" class="success-message">
        <i class="pi pi-check-circle"></i>
        {{ successMessage }}
      </div>

      <!-- Upload Button -->
      <button 
        @click="uploadFile"
        :disabled="!canUpload"
        class="upload-btn"
        :class="{ 'uploading': uploading }"
      >
        <i v-if="uploading" class="pi pi-spin pi-spinner"></i>
        <i v-else class="pi pi-upload"></i>
        {{ uploading ? 'Processing...' : 'Upload & Process' }}
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'POUploader',
  data() {
    return {
      selectedSupplier: '',
      selectedFile: null,
      dragOver: false,
      uploading: false,
      uploadProgress: 0,
      uploadStatusText: '',
      errorMessage: '',
      successMessage: '',
      suppliers: []
    }
  },
  computed: {
    canUpload() {
      return this.selectedSupplier && this.selectedFile && !this.uploading
    }
  },
  async mounted() {
    await this.fetchSuppliers()
  },
  methods: {
    async fetchSuppliers() {
      try {
        const response = await fetch('/api/suppliers/')
        const data = await response.json()
        
        if (response.ok) {
          this.suppliers = data.suppliers
        } else {
          this.errorMessage = 'Failed to load suppliers. Please refresh the page.'
        }
      } catch (error) {
        console.error('Error fetching suppliers:', error)
        this.errorMessage = 'Failed to load suppliers. Please check your connection.'
      }
    },
    
    triggerFileInput() {
      if (!this.uploading) {
        this.$refs.fileInput.click()
      }
    },
    
    handleFileSelect(event) {
      const file = event.target.files[0]
      this.validateAndSetFile(file)
    },
    
    handleDrop(event) {
      event.preventDefault()
      this.dragOver = false
      
      if (this.uploading) return
      
      const files = event.dataTransfer.files
      if (files.length > 0) {
        this.validateAndSetFile(files[0])
      }
    },
    
    handleDragOver(event) {
      event.preventDefault()
      if (!this.uploading) {
        this.dragOver = true
      }
    },
    
    handleDragLeave() {
      this.dragOver = false
    },
    
    validateAndSetFile(file) {
      this.clearMessages()
      
      if (!file) return
      
      // Check file type
      if (file.type !== 'application/pdf') {
        this.errorMessage = 'Please select a PDF file.'
        return
      }
      
      // Check file size (10MB limit)
      const maxSize = 10 * 1024 * 1024 // 10MB in bytes
      if (file.size > maxSize) {
        this.errorMessage = 'File size must be less than 10MB.'
        return
      }
      
      this.selectedFile = file
    },
    
    removeFile() {
      this.selectedFile = null
      this.$refs.fileInput.value = ''
      this.clearMessages()
    },
    
    async uploadFile() {
      if (!this.canUpload) return
      
      this.uploading = true
      this.uploadProgress = 0
      this.uploadStatusText = 'Preparing upload...'
      this.clearMessages()
      
      const formData = new FormData()
      formData.append('file', this.selectedFile)
      formData.append('supplier_id', this.selectedSupplier)
      
      try {
        this.uploadStatusText = 'Uploading file...'
        this.uploadProgress = 25
        
        const response = await fetch('/api/upload-po/', {
          method: 'POST',
          body: formData,
          headers: {
            'X-CSRFToken': this.getCsrfToken()
          }
        })
        
        this.uploadProgress = 50
        this.uploadStatusText = 'Processing with AirParser...'
        
        const result = await response.json()
        
        if (response.ok) {
          this.uploadProgress = 100
          this.uploadStatusText = 'Complete!'
          this.successMessage = `Successfully processed purchase order for ${this.getSupplierName(this.selectedSupplier)}`
          
          // Reset form after success
          setTimeout(() => {
            this.resetForm()
          }, 3000)
        } else {
          throw new Error(result.error || 'Upload failed')
        }
      } catch (error) {
        console.error('Upload error:', error)
        this.errorMessage = error.message || 'An error occurred during upload. Please try again.'
      } finally {
        this.uploading = false
      }
    },
    
    resetForm() {
      this.selectedSupplier = ''
      this.selectedFile = null
      this.$refs.fileInput.value = ''
      this.uploadProgress = 0
      this.uploadStatusText = ''
      this.clearMessages()
    },
    
    clearMessages() {
      this.errorMessage = ''
      this.successMessage = ''
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    },
    
    getSupplierName(id) {
      const supplier = this.suppliers.find(s => s.id === id)
      return supplier ? supplier.name : id
    },
    
    getCsrfToken() {
      // Get CSRF token from Django
      const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1]
      return cookieValue || ''
    }
  }
}
</script>

<style scoped>
.po-uploader-container {
  max-width: 600px;
  margin: 2rem auto;
  padding: 1rem;
}

.upload-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
}

.upload-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 0.5rem 0;
  text-align: center;
}

.upload-subtitle {
  color: #6b7280;
  text-align: center;
  margin: 0 0 2rem 0;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  display: block;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
}

.form-select {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #d1d5db;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-select:disabled {
  background-color: #f9fafb;
  cursor: not-allowed;
}

.file-upload-section {
  margin-bottom: 1.5rem;
}

.file-drop-zone {
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background-color: #fafafa;
}

.file-drop-zone:hover:not(.disabled) {
  border-color: #3b82f6;
  background-color: #f0f9ff;
}

.file-drop-zone.drag-over {
  border-color: #3b82f6;
  background-color: #eff6ff;
}

.file-drop-zone.has-file {
  border-color: #10b981;
  background-color: #f0fdf4;
}

.file-drop-zone.disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.file-input-hidden {
  display: none;
}

.drop-zone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.upload-icon {
  font-size: 3rem;
  color: #9ca3af;
  margin-bottom: 1rem;
}

.upload-text {
  font-size: 1.1rem;
  color: #374151;
  margin: 0 0 0.25rem 0;
}

.upload-hint {
  color: #6b7280;
  font-size: 0.9rem;
  margin: 0;
}

.file-selected {
  display: flex;
  align-items: center;
  gap: 1rem;
  text-align: left;
}

.file-icon {
  font-size: 2rem;
  color: #dc2626;
}

.file-info {
  flex: 1;
}

.file-name {
  font-weight: 600;
  color: #374151;
  margin: 0 0 0.25rem 0;
}

.file-size {
  color: #6b7280;
  font-size: 0.9rem;
  margin: 0;
}

.remove-file-btn {
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: color 0.2s;
}

.remove-file-btn:hover {
  color: #dc2626;
}

.upload-progress {
  margin-bottom: 1.5rem;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background-color: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background-color: #3b82f6;
  transition: width 0.3s ease;
}

.progress-text {
  text-align: center;
  color: #6b7280;
  font-size: 0.9rem;
  margin: 0;
}

.error-message, .success-message {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.error-message {
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
}

.success-message {
  background-color: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #16a34a;
}

.upload-btn {
  width: 100%;
  padding: 0.875rem 1.5rem;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.upload-btn:hover:not(:disabled) {
  background-color: #2563eb;
}

.upload-btn:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}

.upload-btn.uploading {
  background-color: #1d4ed8;
}
</style>
