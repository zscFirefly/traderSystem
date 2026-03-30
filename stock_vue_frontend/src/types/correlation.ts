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
  error?: string
}
