export type CorrelationMethod = 'pearson' | 'spearman' | 'kendall'

export interface CorrelationStockInput {
  stock_code: string
  stock_name: string
}

export interface CorrelationMatrixResult {
  matrix: Record<string, Record<string, number>>
}

export interface SignificanceResult {
  matrix: Record<string, Record<string, number>>
}

export interface MultiStockCorrelationPayload {
  stocks: CorrelationStockInput[]
  trading_days?: number
  period?: string
  include_heatmaps?: boolean
}

export interface MultiStockCorrelationResponse {
  success: boolean
  target_stocks: Array<{
    symbol: string
    name: string
  }>
  time_range: {
    start_date: string
    end_date: string
  }
  trading_days: number
  period: string
  returns_count: number
  correlation_results: Partial<Record<CorrelationMethod, CorrelationMatrixResult>>
  significance_result?: SignificanceResult | null
  failed_stocks?: Array<{
    symbol: string
    name: string
    reason: string
  }>
  error?: string
}

export interface CorrelationPresetItem {
  id: string
  name: string
  description: string
  stocks: CorrelationStockInput[]
  trading_days: number
  period: string
  include_heatmaps: boolean
  is_pinned: boolean
  created_by: string
  created_at: string
  updated_by: string
  updated_at: string
  is_deleted: string
}

export interface CorrelationPresetPayload {
  name: string
  description?: string
  stocks: CorrelationStockInput[]
  trading_days: number
  period: string
  include_heatmaps?: boolean
  is_pinned?: boolean
  created_by?: string
  updated_by?: string
}

export interface CorrelationPresetListResponse {
  success: boolean
  total: number
  results: CorrelationPresetItem[]
  error?: string
}

export interface CorrelationPresetMutationResponse {
  success: boolean
  item?: CorrelationPresetItem
  error?: string
}
