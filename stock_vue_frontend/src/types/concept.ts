export interface ConceptStockItem {
  stock_name: string
  stock_code: string
  concepts: string[]
  centrality: number
  related_stocks: string[]
}

export interface ConceptStocksResponse {
  success: boolean
  concept: string
  total_count?: number
  graph_stats?: {
    nodes: number
    edges: number
  }
  results: ConceptStockItem[]
  message?: string
  error?: string
}
