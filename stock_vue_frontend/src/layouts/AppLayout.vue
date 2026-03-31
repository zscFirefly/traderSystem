<template>
  <div class="app-shell">
    <AppSidebar />
    <div class="app-main">
      <AppHeader />
      <main class="page-content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import AppHeader from '@/layouts/components/AppHeader.vue'
import AppSidebar from '@/layouts/components/AppSidebar.vue'
</script>
