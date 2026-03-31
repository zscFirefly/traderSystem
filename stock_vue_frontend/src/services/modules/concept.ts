import http from '@/services/http'

export function getConceptStocks(concept: string, topk = 20, minWeight = 1) {
  return http.get('/concept_stocks', {
    params: {
      concept,
      topk,
      min_weight: minWeight
    }
  })
}
