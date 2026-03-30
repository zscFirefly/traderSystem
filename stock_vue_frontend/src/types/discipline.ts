export interface DisciplineRuleItem {
  id: string
  rule_title: string
  rule_type: string
  rule_content: string
  priority: string
  strong_reminder: string
  status: string
  created_by: string
  created_at: string
  updated_by: string
  updated_at: string
  is_deleted: string
}

export interface DisciplineLessonItem {
  id: string
  lesson_time: string
  target_name: string
  target_code: string
  concept_name: string
  mistake_action: string
  original_thought: string
  actual_outcome: string
  trigger_reason: string
  linked_rule: string
  improvement_action: string
  severity: string
  show_on_dashboard: string
  created_by: string
  created_at: string
  updated_by: string
  updated_at: string
  is_deleted: string
}

export interface DisciplineListResponse<T> {
  success: boolean
  total: number
  results: T[]
  error?: string
}

export interface CreateDisciplineRulePayload {
  rule_title: string
  rule_type: string
  rule_content: string
  priority: string
  strong_reminder: boolean
  status: string
  created_by?: string
  updated_by?: string
}

export interface CreateDisciplineLessonPayload {
  lesson_time: string
  target_name?: string
  target_code?: string
  concept_name?: string
  mistake_action: string
  original_thought?: string
  actual_outcome: string
  trigger_reason?: string
  linked_rule?: string
  improvement_action?: string
  severity: string
  show_on_dashboard: boolean
  created_by?: string
  updated_by?: string
}

export interface DisciplineCreateResponse<T> {
  success: boolean
  item?: T
  error?: string
}

export interface DisciplineDeleteResponse<T> {
  success: boolean
  item?: T
  error?: string
}
