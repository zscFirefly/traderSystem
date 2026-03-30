export type AlertSeverity = 'low' | 'medium' | 'high'
export type AlertStatus = 'pending' | 'tracking' | 'closed'

export interface AlertItem {
  id: string
  event_time: string
  event_title: string
  potential_risk: string
  stock_name: string
  stock_code: string
  concept_name: string
  severity: AlertSeverity | string
  status: AlertStatus | string
  notes: string
  created_by: string
  created_at: string
  updated_by: string
  updated_at: string
  is_deleted: string
}

export interface AlertsListResponse {
  success: boolean
  total: number
  results: AlertItem[]
  error?: string
}

export interface CreateAlertPayload {
  event_time: string
  event_title: string
  potential_risk: string
  stock_name?: string
  stock_code?: string
  concept_name?: string
  severity?: AlertSeverity | string
  status?: AlertStatus | string
  notes?: string
  created_by?: string
  updated_by?: string
}

export interface CreateAlertResponse {
  success: boolean
  item?: AlertItem
  error?: string
}

export interface DeleteAlertResponse {
  success: boolean
  item?: AlertItem
  error?: string
}
