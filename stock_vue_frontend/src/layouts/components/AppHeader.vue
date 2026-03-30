<template>
  <header class="app-header">
    <div>
      <p class="header-eyebrow">多模块研究工作台</p>
      <h2 class="header-title">{{ title }}</h2>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const title = computed(() => (route.meta.title as string) || '总览')
</script>
