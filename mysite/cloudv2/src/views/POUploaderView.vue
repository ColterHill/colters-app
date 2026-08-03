<template>
  <div class="po-uploader-view">
    <POUploader />
  </div>
</template>

<script>
import POUploader from '../components/POUploader.vue'

export default {
  name: 'POUploaderView',
  components: {
    POUploader
  }
}
</script>

<style scoped>
.po-uploader-view {
  min-height: 100vh;
  background-color: #f9fafb;
  padding: 2rem 1rem;
}
</style>
