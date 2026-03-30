<template>
  <aside class="detail-drawer" :class="{ 'detail-drawer-open': appStore.drawerOpen }">
    <div class="drawer-header">
      <div>
        <p class="drawer-eyebrow">详情抽屉</p>
        <h3 class="drawer-title">{{ appStore.drawerTitle }}</h3>
      </div>
      <button class="ghost-button" @click="appStore.closeDrawer">关闭</button>
    </div>
    <div v-if="appStore.hasDrawerContent" class="drawer-content">
      <pre>{{ JSON.stringify(appStore.drawerContent, null, 2) }}</pre>
    </div>
    <div v-else class="drawer-empty">选择股票、概念或事件后在这里查看详情。</div>
  </aside>
</template>

<script setup lang="ts">
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
</script>
