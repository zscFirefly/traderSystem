<template>
  <div class="page-stack">
    <PageSection title="相关性分析" description="单独页面承载股票池、方法切换、矩阵图和显著性图。">
      <CorrelationPanel
        editable
        title="独立相关性分析"
        description="手动维护股票池后发起分析，适合脱离股票关联页单独比较一组标的。"
      />
    </PageSection>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

import CorrelationPanel from '@/components/business/correlation/CorrelationPanel.vue'
import PageSection from '@/components/common/PageSection.vue'
import { useCorrelationStore } from '@/stores/correlation'

const correlationStore = useCorrelationStore()

onMounted(() => {
  correlationStore.reset()
})
</script>
