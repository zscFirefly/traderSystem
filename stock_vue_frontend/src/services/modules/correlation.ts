import http from '@/services/http'
import type { MultiStockCorrelationPayload } from '@/types/correlation'

const CORRELATION_TIMEOUT_MS = Number(import.meta.env.VITE_CORRELATION_TIMEOUT_MS || 300000)

export function getCorrelationMatrix(payload: MultiStockCorrelationPayload) {
  return http.post('/api/multi_stock_correlation', payload, {
    timeout: CORRELATION_TIMEOUT_MS
  })
}
