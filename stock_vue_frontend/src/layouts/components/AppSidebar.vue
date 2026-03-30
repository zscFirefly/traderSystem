<template>
  <aside class="app-sidebar">
    <div class="brand-block">
      <p class="brand-eyebrow">Workspace</p>
      <h1 class="brand-title">Stock Research</h1>
    </div>
    <nav class="nav-list">
      <RouterLink
        v-for="item in navigationItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        active-class="nav-item-active"
      >
        {{ item.label }}
      </RouterLink>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'

import { navigationItems } from '@/constants/navigation'
</script>
