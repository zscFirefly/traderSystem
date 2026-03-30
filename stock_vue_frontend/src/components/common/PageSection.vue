<template>
  <section class="page-section">
    <div class="section-header">
      <div class="section-title-group">
        <h3 class="section-title">
          {{ title }}
          <span v-if="description" class="section-info" tabindex="0" :aria-label="description">
            <span class="section-info-icon">i</span>
            <span class="section-tooltip" role="tooltip">{{ description }}</span>
          </span>
        </h3>
      </div>
      <slot name="actions" />
    </div>
    <div class="section-body">
      <slot />
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>
