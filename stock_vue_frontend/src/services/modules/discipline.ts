import http from '@/services/http'
import type { CreateDisciplineLessonPayload, CreateDisciplineRulePayload } from '@/types/discipline'

export function getDisciplineRules(limit?: number) {
  return http.get('/discipline/rules', {
    params: limit ? { limit } : undefined
  })
}

export function createDisciplineRule(payload: CreateDisciplineRulePayload) {
  return http.post('/discipline/rules', payload)
}

export function updateDisciplineRule(ruleId: string, payload: CreateDisciplineRulePayload) {
  return http.put(`/discipline/rules/${ruleId}`, payload)
}

export function deleteDisciplineRule(ruleId: string, operator?: string) {
  return http.delete(`/discipline/rules/${ruleId}`, {
    data: operator ? { updated_by: operator } : undefined
  })
}

export function getDisciplineLessons(limit?: number, dashboardOnly = false) {
  return http.get('/discipline/lessons', {
    params: {
      ...(limit ? { limit } : {}),
      dashboard_only: dashboardOnly
    }
  })
}

export function createDisciplineLesson(payload: CreateDisciplineLessonPayload) {
  return http.post('/discipline/lessons', payload)
}

export function updateDisciplineLesson(lessonId: string, payload: CreateDisciplineLessonPayload) {
  return http.put(`/discipline/lessons/${lessonId}`, payload)
}

export function deleteDisciplineLesson(lessonId: string, operator?: string) {
  return http.delete(`/discipline/lessons/${lessonId}`, {
    data: operator ? { updated_by: operator } : undefined
  })
}
