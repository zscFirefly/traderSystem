<template>
  <article class="metric-card">
    <p class="metric-label">{{ label }}</p>
    <strong class="metric-value">{{ value }}</strong>
    <p v-if="note" class="metric-note">{{ note }}</p>
  </article>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  value: string
  note?: string
}>()
</script>
