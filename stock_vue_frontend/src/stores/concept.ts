import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { getConceptStocks } from '@/services/modules/concept'
import type { ConceptStockItem, ConceptStocksResponse } from '@/types/concept'

export const useConceptStore = defineStore('concept', () => {
  const query = ref('')
  const topk = ref(20)
  const minWeight = ref(1)
  const loading = ref(false)
  const error = ref('')
  const message = ref('')
  const selectedConcept = ref('')
  const totalCount = ref(0)
  const graphStats = ref<{ nodes: number; edges: number } | null>(null)
  const results = ref<ConceptStockItem[]>([])

  const hasResults = computed(() => results.value.length > 0)

  async function fetchConceptStocks(conceptName?: string) {
    const target = (conceptName ?? query.value).trim()
    if (!target) {
      error.value = '请输入概念名称'
      return
    }

    loading.value = true
    error.value = ''
    message.value = ''

    try {
      const response = await getConceptStocks(target, topk.value, minWeight.value)
      const payload = response.data as ConceptStocksResponse
      if (!payload.success) {
        throw new Error(payload.error || '查询失败')
      }

      selectedConcept.value = payload.concept
      totalCount.value = payload.total_count ?? payload.results.length
      graphStats.value = payload.graph_stats ?? null
      results.value = payload.results ?? []
      message.value = payload.message ?? ''
      query.value = payload.concept
    } catch (err) {
      const nextMessage = err instanceof Error ? err.message : '查询失败，请稍后重试'
      error.value = nextMessage
      results.value = []
      totalCount.value = 0
      graphStats.value = null
      message.value = ''
    } finally {
      loading.value = false
    }
  }

  return {
    query,
    topk,
    minWeight,
    loading,
    error,
    message,
    selectedConcept,
    totalCount,
    graphStats,
    results,
    hasResults,
    fetchConceptStocks
  }
})
