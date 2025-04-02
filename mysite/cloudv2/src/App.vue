<template>
  <div class="wrapper">
    
    <Sidebar v-if="isOpen" class="sidebar"/>
    <nav class="page">
      <router-view />
    </nav>
    
  </div>
  
</template>

<script>
import Sidebar from './components/sidebar/Sidebar.vue';
export default {
  components: {
    Sidebar
  },
  data() {
        return {
            isOpen: true
        }
    },
    methods: {
        toggleSidebar() {
            this.isOpen = !this.isOpen
        }
    },
}
</script>

<style scoped>
.wrapper {
  display: block;
  justify-content: space-between; 
}

.navButton {
  margin-left: 20px;
}

.sidebar {
  width: 100%;
}

.page {
  width: 100%;
}

.sidebar-icon {
  padding: 10px;
  margin-left: 15px;
  background-color: #304c7a;
  height: 40px;
  width: 40px;
  justify-content: center;
  border-radius: 10px;
  text-align: center;
  cursor: pointer;

}

</style>
