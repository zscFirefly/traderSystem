import http from '@/services/http'
import type {
  CorrelationPresetPayload,
  MultiStockCorrelationPayload
} from '@/types/correlation'

const CORRELATION_TIMEOUT_MS = Number(import.meta.env.VITE_CORRELATION_TIMEOUT_MS || 300000)

export function getCorrelationMatrix(payload: MultiStockCorrelationPayload) {
  return http.post('/multi_stock_correlation', payload, {
    timeout: CORRELATION_TIMEOUT_MS
  })
}

export function getCorrelationPresets(limit?: number) {
  return http.get('/correlation/presets', {
    params: limit ? { limit } : undefined
  })
}

export function createCorrelationPreset(payload: CorrelationPresetPayload) {
  return http.post('/correlation/presets', payload)
}

export function updateCorrelationPreset(presetId: string, payload: CorrelationPresetPayload) {
  return http.put(`/correlation/presets/${presetId}`, payload)
}

export function deleteCorrelationPreset(presetId: string, operator?: string) {
  return http.delete(`/correlation/presets/${presetId}`, {
    data: operator ? { updated_by: operator } : undefined
  })
}
