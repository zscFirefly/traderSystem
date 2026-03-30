import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { getRelatedStocks, searchStocks } from '@/services/modules/stock'
import type { RelatedStockItem, RelatedStocksResponse } from '@/types/stock'

export const useStockStore = defineStore('stock', () => {
  const query = ref('')
  const suggestions = ref<string[]>([])
  const loadingSuggestions = ref(false)
  const loadingRelated = ref(false)
  const error = ref('')
  const selectedStock = ref('')
  const targetStockCode = ref('')
  const relatedStocks = ref<RelatedStockItem[]>([])
  const topk = ref(10)
  const match300 = ref(false)

  const hasResults = computed(() => relatedStocks.value.length > 0)

  async function fetchSuggestions(keyword: string) {
    query.value = keyword
    if (!keyword.trim()) {
      suggestions.value = []
      return
    }

    loadingSuggestions.value = true
    try {
      const response = await searchStocks(keyword.trim())
      suggestions.value = Array.isArray(response.data) ? response.data : []
    } catch (err) {
      console.error('Failed to fetch stock suggestions', err)
      suggestions.value = []
    } finally {
      loadingSuggestions.value = false
    }
  }

  async function fetchRelatedStocks(stockName?: string) {
    const target = (stockName ?? selectedStock.value).trim()
    if (!target) {
      error.value = '请输入股票名称'
      return
    }

    loadingRelated.value = true
    error.value = ''

    try {
      const response = await getRelatedStocks(target, topk.value, match300.value)
      const payload = response.data as RelatedStocksResponse
      if (!payload.success) {
        throw new Error(payload.error || '查询失败')
      }

      selectedStock.value = payload.target_stock
      targetStockCode.value = payload.target_stock_code
      relatedStocks.value = payload.results || []
      suggestions.value = []
    } catch (err) {
      const message = err instanceof Error ? err.message : '查询失败，请稍后重试'
      error.value = message
      relatedStocks.value = []
      targetStockCode.value = ''
    } finally {
      loadingRelated.value = false
    }
  }

  function selectSuggestion(stockName: string) {
    query.value = stockName
    selectedStock.value = stockName
    suggestions.value = []
  }

  function clearSuggestions() {
    suggestions.value = []
  }

  return {
    query,
    suggestions,
    loadingSuggestions,
    loadingRelated,
    error,
    selectedStock,
    targetStockCode,
    relatedStocks,
    topk,
    match300,
    hasResults,
    fetchSuggestions,
    fetchRelatedStocks,
    selectSuggestion,
    clearSuggestions
  }
})
