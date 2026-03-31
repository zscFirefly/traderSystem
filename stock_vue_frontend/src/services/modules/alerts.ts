import http from '@/services/http'
import type { CreateAlertPayload } from '@/types/alert'

export function getAlerts(limit?: number) {
  return http.get('/alerts', {
    params: limit ? { limit } : undefined
  })
}

export function createAlert(payload: CreateAlertPayload) {
  return http.post('/alerts', payload)
}

export function updateAlert(alertId: string, payload: CreateAlertPayload) {
  return http.put(`/alerts/${alertId}`, payload)
}

export function deleteAlert(alertId: string, operator?: string) {
  return http.delete(`/alerts/${alertId}`, {
    data: operator ? { updated_by: operator } : undefined
  })
}
