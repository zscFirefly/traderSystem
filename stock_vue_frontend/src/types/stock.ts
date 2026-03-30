export interface RelatedStockItem {
  stock_name: string
  stock_code: string
  count: number
  dates: string[]
  concepts: string[]
}

export interface RelatedStocksResponse {
  success: boolean
  target_stock: string
  target_stock_code: string
  results: RelatedStockItem[]
  error?: string
}
