import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

import { getCorrelationMatrix } from '@/services/modules/correlation'
import type {
  CorrelationMethod,
  CorrelationStockInput,
  MultiStockCorrelationResponse
} from '@/types/correlation'

const METHOD_ORDER: CorrelationMethod[] = ['pearson', 'spearman', 'kendall']

export const useCorrelationStore = defineStore('correlation', () => {
  const expanded = ref(false)
  const loading = ref(false)
  const error = ref('')
  const activeMethod = ref<CorrelationMethod>('pearson')
  const tradingDays = ref(10)
  const period = ref('5')
  const lastRequestKey = ref('')
  const targetStocks = ref<Array<{ symbol: string; name: string }>>([])
  const timeRange = ref<{ start_date: string; end_date: string } | null>(null)
  const returnsCount = ref(0)
  const failedStocks = ref<MultiStockCorrelationResponse['failed_stocks']>([])
  const correlationResults = ref<MultiStockCorrelationResponse['correlation_results']>({})
  const significanceResult = ref<MultiStockCorrelationResponse['significance_result']>(null)

  const availableMethods = computed(() =>
    METHOD_ORDER.filter((method) => Boolean(correlationResults.value[method]))
  )

  const currentResult = computed(() => correlationResults.value[activeMethod.value] ?? null)
  const currentMatrix = computed(() => currentResult.value?.matrix ?? null)
  const significanceMatrix = computed(() => significanceResult.value?.matrix ?? null)

  const hasData = computed(() => availableMethods.value.length > 0)

  function setExpanded(value: boolean) {
    expanded.value = value
  }

  function setActiveMethod(method: CorrelationMethod) {
    if (availableMethods.value.includes(method)) {
      activeMethod.value = method
    }
  }

  function setError(message: string) {
    error.value = message
  }

  function reset() {
    expanded.value = false
    loading.value = false
    error.value = ''
    activeMethod.value = 'pearson'
    lastRequestKey.value = ''
    targetStocks.value = []
    timeRange.value = null
    returnsCount.value = 0
    failedStocks.value = []
    correlationResults.value = {}
    significanceResult.value = null
  }

  async function fetchCorrelation(stocks: CorrelationStockInput[], force = false) {
    if (stocks.length < 2) {
      error.value = '至少需要两只股票才能进行相关性分析'
      return false
    }

    const requestKey = JSON.stringify({
      stocks,
      tradingDays: tradingDays.value,
      period: period.value
    })

    if (!force && requestKey === lastRequestKey.value && hasData.value) {
      error.value = ''
      return true
    }

    loading.value = true
    error.value = ''

    try {
      const response = await getCorrelationMatrix({
        stocks,
        trading_days: tradingDays.value,
        period: period.value,
        include_heatmaps: false
      })
      const payload = response.data as MultiStockCorrelationResponse
      if (!payload.success) {
        throw new Error(payload.error || '相关性分析失败')
      }

      correlationResults.value = payload.correlation_results ?? {}
      significanceResult.value = payload.significance_result ?? null
      targetStocks.value = payload.target_stocks ?? []
      timeRange.value = payload.time_range
      returnsCount.value = payload.returns_count ?? 0
      failedStocks.value = payload.failed_stocks ?? []
      lastRequestKey.value = requestKey

      const preferredMethod = METHOD_ORDER.find((method) => payload.correlation_results?.[method])
      if (preferredMethod) {
        activeMethod.value = preferredMethod
      }

      return true
    } catch (err) {
      let message = err instanceof Error ? err.message : '相关性分析失败，请稍后重试'
      if (axios.isAxiosError(err)) {
        message = err.response?.data?.error || err.message || message
        failedStocks.value = err.response?.data?.failed_stocks ?? []
      } else {
        failedStocks.value = []
      }
      error.value = message
      correlationResults.value = {}
      significanceResult.value = null
      targetStocks.value = []
      timeRange.value = null
      returnsCount.value = 0
      lastRequestKey.value = ''
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    expanded,
    loading,
    error,
    activeMethod,
    tradingDays,
    period,
    targetStocks,
    timeRange,
    returnsCount,
    failedStocks,
    correlationResults,
    significanceResult,
    availableMethods,
    currentResult,
    currentMatrix,
    significanceMatrix,
    hasData,
    setExpanded,
    setActiveMethod,
    setError,
    reset,
    fetchCorrelation
  }
})
