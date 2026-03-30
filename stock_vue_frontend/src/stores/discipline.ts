import { computed, reactive, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  createDisciplineLesson,
  createDisciplineRule,
  deleteDisciplineLesson,
  deleteDisciplineRule,
  getDisciplineLessons,
  getDisciplineRules,
  updateDisciplineLesson,
  updateDisciplineRule
} from '@/services/modules/discipline'
import type {
  CreateDisciplineLessonPayload,
  CreateDisciplineRulePayload,
  DisciplineCreateResponse,
  DisciplineDeleteResponse,
  DisciplineLessonItem,
  DisciplineListResponse,
  DisciplineRuleItem
} from '@/types/discipline'

function createEmptyRuleForm() {
  return {
    rule_title: '',
    rule_type: '开仓',
    rule_content: '',
    priority: 'high',
    strong_reminder: true,
    status: 'active',
    created_by: 'admin'
  }
}

function createEmptyLessonForm() {
  return {
    lesson_time: '',
    target_name: '',
    target_code: '',
    concept_name: '',
    mistake_action: '',
    original_thought: '',
    actual_outcome: '',
    trigger_reason: '',
    linked_rule: '',
    improvement_action: '',
    severity: 'high',
    show_on_dashboard: true,
    created_by: 'admin'
  }
}

export const useDisciplineStore = defineStore('discipline', () => {
  const loadingRules = ref(false)
  const loadingLessons = ref(false)
  const submittingRule = ref(false)
  const submittingLesson = ref(false)
  const error = ref('')
  const successMessage = ref('')
  const editingRuleId = ref('')
  const editingLessonId = ref('')
  const rules = ref<DisciplineRuleItem[]>([])
  const lessons = ref<DisciplineLessonItem[]>([])
  const dashboardRules = ref<DisciplineRuleItem[]>([])
  const dashboardLessons = ref<DisciplineLessonItem[]>([])
  const ruleForm = reactive(createEmptyRuleForm())
  const lessonForm = reactive(createEmptyLessonForm())

  const hasRules = computed(() => rules.value.length > 0)
  const hasLessons = computed(() => lessons.value.length > 0)
  const isEditingRule = computed(() => Boolean(editingRuleId.value))
  const isEditingLesson = computed(() => Boolean(editingLessonId.value))

  function formatDatetimeForInput(value: string) {
    if (!value) {
      return ''
    }
    return value.slice(0, 16).replace(' ', 'T')
  }

  async function fetchRules(limit?: number, target: 'default' | 'dashboard' = 'default') {
    loadingRules.value = true
    error.value = ''
    try {
      const response = await getDisciplineRules(limit)
      const payload = response.data as DisciplineListResponse<DisciplineRuleItem>
      if (!payload.success) {
        throw new Error(payload.error || '加载纪律清单失败')
      }

      if (target === 'dashboard') {
        dashboardRules.value = payload.results ?? []
      } else {
        rules.value = payload.results ?? []
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载纪律清单失败'
      if (target === 'dashboard') {
        dashboardRules.value = []
      } else {
        rules.value = []
      }
    } finally {
      loadingRules.value = false
    }
  }

  async function fetchLessons(limit?: number, target: 'default' | 'dashboard' = 'default') {
    loadingLessons.value = true
    error.value = ''
    try {
      const response = await getDisciplineLessons(limit, target === 'dashboard')
      const payload = response.data as DisciplineListResponse<DisciplineLessonItem>
      if (!payload.success) {
        throw new Error(payload.error || '加载血泪教训失败')
      }

      if (target === 'dashboard') {
        dashboardLessons.value = payload.results ?? []
      } else {
        lessons.value = payload.results ?? []
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载血泪教训失败'
      if (target === 'dashboard') {
        dashboardLessons.value = []
      } else {
        lessons.value = []
      }
    } finally {
      loadingLessons.value = false
    }
  }

  async function submitRule() {
    submittingRule.value = true
    error.value = ''
    successMessage.value = ''
    try {
      const payload: CreateDisciplineRulePayload = {
        rule_title: ruleForm.rule_title,
        rule_type: ruleForm.rule_type,
        rule_content: ruleForm.rule_content,
        priority: ruleForm.priority,
        strong_reminder: ruleForm.strong_reminder,
        status: ruleForm.status,
        created_by: ruleForm.created_by,
        updated_by: ruleForm.created_by
      }
      const response = editingRuleId.value
        ? await updateDisciplineRule(editingRuleId.value, payload)
        : await createDisciplineRule(payload)
      const result = response.data as DisciplineCreateResponse<DisciplineRuleItem>
      if (!result.success || !result.item) {
        throw new Error(result.error || '保存纪律清单失败')
      }

      successMessage.value = editingRuleId.value ? '纪律清单已更新' : '纪律清单已保存'
      resetRuleForm()
      await fetchRules()
      await fetchRules(5, 'dashboard')
    } catch (err) {
      error.value = err instanceof Error ? err.message : '保存纪律清单失败'
    } finally {
      submittingRule.value = false
    }
  }

  async function submitLesson() {
    submittingLesson.value = true
    error.value = ''
    successMessage.value = ''
    try {
      const payload: CreateDisciplineLessonPayload = {
        lesson_time: lessonForm.lesson_time,
        target_name: lessonForm.target_name,
        target_code: lessonForm.target_code,
        concept_name: lessonForm.concept_name,
        mistake_action: lessonForm.mistake_action,
        original_thought: lessonForm.original_thought,
        actual_outcome: lessonForm.actual_outcome,
        trigger_reason: lessonForm.trigger_reason,
        linked_rule: lessonForm.linked_rule,
        improvement_action: lessonForm.improvement_action,
        severity: lessonForm.severity,
        show_on_dashboard: lessonForm.show_on_dashboard,
        created_by: lessonForm.created_by,
        updated_by: lessonForm.created_by
      }
      const response = editingLessonId.value
        ? await updateDisciplineLesson(editingLessonId.value, payload)
        : await createDisciplineLesson(payload)
      const result = response.data as DisciplineCreateResponse<DisciplineLessonItem>
      if (!result.success || !result.item) {
        throw new Error(result.error || '保存血泪教训失败')
      }

      successMessage.value = editingLessonId.value ? '血泪教训已更新' : '血泪教训已保存'
      resetLessonForm()
      await fetchLessons()
      await fetchLessons(5, 'dashboard')
    } catch (err) {
      error.value = err instanceof Error ? err.message : '保存血泪教训失败'
    } finally {
      submittingLesson.value = false
    }
  }

  function resetRuleForm() {
    Object.assign(ruleForm, createEmptyRuleForm())
    editingRuleId.value = ''
  }

  function resetLessonForm() {
    Object.assign(lessonForm, createEmptyLessonForm())
    editingLessonId.value = ''
  }

  function startEditRule(item: DisciplineRuleItem) {
    editingRuleId.value = item.id
    Object.assign(ruleForm, {
      rule_title: item.rule_title,
      rule_type: item.rule_type,
      rule_content: item.rule_content,
      priority: item.priority,
      strong_reminder: item.strong_reminder === '1',
      status: item.status,
      created_by: item.updated_by || item.created_by || 'admin'
    })
  }

  function startEditLesson(item: DisciplineLessonItem) {
    editingLessonId.value = item.id
    Object.assign(lessonForm, {
      lesson_time: formatDatetimeForInput(item.lesson_time),
      target_name: item.target_name,
      target_code: item.target_code,
      concept_name: item.concept_name,
      mistake_action: item.mistake_action,
      original_thought: item.original_thought,
      actual_outcome: item.actual_outcome,
      trigger_reason: item.trigger_reason,
      linked_rule: item.linked_rule,
      improvement_action: item.improvement_action,
      severity: item.severity,
      show_on_dashboard: item.show_on_dashboard === '1',
      created_by: item.updated_by || item.created_by || 'admin'
    })
  }

  async function removeRule(item: DisciplineRuleItem) {
    submittingRule.value = true
    error.value = ''
    successMessage.value = ''
    try {
      const response = await deleteDisciplineRule(item.id, ruleForm.created_by || item.updated_by || item.created_by)
      const result = response.data as DisciplineDeleteResponse<DisciplineRuleItem>
      if (!result.success) {
        throw new Error(result.error || '删除纪律清单失败')
      }

      if (editingRuleId.value === item.id) {
        resetRuleForm()
      }

      successMessage.value = '纪律清单已删除'
      await fetchRules()
      await fetchRules(5, 'dashboard')
    } catch (err) {
      error.value = err instanceof Error ? err.message : '删除纪律清单失败'
    } finally {
      submittingRule.value = false
    }
  }

  async function removeLesson(item: DisciplineLessonItem) {
    submittingLesson.value = true
    error.value = ''
    successMessage.value = ''
    try {
      const response = await deleteDisciplineLesson(item.id, lessonForm.created_by || item.updated_by || item.created_by)
      const result = response.data as DisciplineDeleteResponse<DisciplineLessonItem>
      if (!result.success) {
        throw new Error(result.error || '删除血泪教训失败')
      }

      if (editingLessonId.value === item.id) {
        resetLessonForm()
      }

      successMessage.value = '血泪教训已删除'
      await fetchLessons()
      await fetchLessons(5, 'dashboard')
    } catch (err) {
      error.value = err instanceof Error ? err.message : '删除血泪教训失败'
    } finally {
      submittingLesson.value = false
    }
  }
  return {
    loadingRules,
    loadingLessons,
    submittingRule,
    submittingLesson,
    error,
    successMessage,
    editingRuleId,
    editingLessonId,
    rules,
    lessons,
    dashboardRules,
    dashboardLessons,
    ruleForm,
    lessonForm,
    hasRules,
    hasLessons,
    isEditingRule,
    isEditingLesson,
    fetchRules,
    fetchLessons,
    submitRule,
    submitLesson,
    resetRuleForm,
    resetLessonForm,
    startEditRule,
    startEditLesson,
    removeRule,
    removeLesson
  }
})
