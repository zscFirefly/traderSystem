import http from '@/services/http'
import type { RelatedStocksResponse } from '@/types/stock'

export function searchStocks(query: string) {
  return http.get<string[]>('/api/search_stocks', { params: { query } })
}

export function getRelatedStocks(stock: string, topk = 10, match300 = false) {
  return http.get<RelatedStocksResponse>('/api/related_stocks', {
    params: {
      stock,
      topk,
      match_300: match300
    }
  })
}
