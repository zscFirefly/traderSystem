import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', () => {
  const drawerOpen = ref(false)
  const drawerTitle = ref('详情')
  const drawerContent = ref<unknown | null>(null)

  function openDrawer(title: string, payload: unknown) {
    drawerTitle.value = title
    drawerContent.value = payload
    drawerOpen.value = true
  }

  function closeDrawer() {
    drawerOpen.value = false
  }

  const hasDrawerContent = computed(() => Boolean(drawerContent.value))

  return {
    drawerOpen,
    drawerTitle,
    drawerContent,
    hasDrawerContent,
    openDrawer,
    closeDrawer
  }
})
