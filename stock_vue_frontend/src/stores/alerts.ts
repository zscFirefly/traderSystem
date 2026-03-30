import { computed, reactive, ref } from 'vue'
import { defineStore } from 'pinia'

import { createAlert, deleteAlert, getAlerts, updateAlert } from '@/services/modules/alerts'
import type {
  AlertItem,
  AlertsListResponse,
  CreateAlertPayload,
  CreateAlertResponse,
  DeleteAlertResponse
} from '@/types/alert'

function createEmptyForm() {
  return {
    event_time: '',
    event_title: '',
    potential_risk: '',
    stock_name: '',
    stock_code: '',
    concept_name: '',
    severity: 'medium',
    status: 'pending',
    notes: '',
    created_by: 'admin'
  }
}

export const useAlertsStore = defineStore('alerts', () => {
  const loading = ref(false)
  const submitting = ref(false)
  const error = ref('')
  const successMessage = ref('')
  const editingAlertId = ref('')
  const items = ref<AlertItem[]>([])
  const previewItems = ref<AlertItem[]>([])
  const totalCount = ref(0)
  const form = reactive(createEmptyForm())

  const hasItems = computed(() => items.value.length > 0)
  const hasPreviewItems = computed(() => previewItems.value.length > 0)
  const highRiskCount = computed(() => items.value.filter((item) => item.severity === 'high').length)
  const isEditing = computed(() => Boolean(editingAlertId.value))

  function formatEventTimeForInput(value: string) {
    if (!value) {
      return ''
    }

    return value.slice(0, 16).replace(' ', 'T')
  }

  async function fetchAlerts(limit?: number, target: 'default' | 'preview' = 'default') {
    loading.value = true
    error.value = ''

    try {
      const response = await getAlerts(limit)
      const payload = response.data as AlertsListResponse
      if (!payload.success) {
        throw new Error(payload.error || '加载事件提醒失败')
      }

      if (target === 'preview') {
        previewItems.value = payload.results ?? []
      } else {
        items.value = payload.results ?? []
      }

      totalCount.value = payload.total ?? (payload.results?.length ?? 0)
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载事件提醒失败'
      if (target === 'preview') {
        previewItems.value = []
      } else {
        items.value = []
      }
    } finally {
      loading.value = false
    }
  }

  async function submitAlert() {
    submitting.value = true
    error.value = ''
    successMessage.value = ''

    try {
      const payload: CreateAlertPayload = {
        event_time: form.event_time,
        event_title: form.event_title,
        potential_risk: form.potential_risk,
        stock_name: form.stock_name,
        stock_code: form.stock_code,
        concept_name: form.concept_name,
        severity: form.severity,
        status: form.status,
        notes: form.notes,
        created_by: form.created_by,
        updated_by: form.created_by
      }

      const response = editingAlertId.value
        ? await updateAlert(editingAlertId.value, payload)
        : await createAlert(payload)
      const result = response.data as CreateAlertResponse
      if (!result.success || !result.item) {
        throw new Error(result.error || '保存事件提醒失败')
      }

      successMessage.value = editingAlertId.value ? '事件提醒已更新' : '事件提醒已保存'
      resetForm()
      await fetchAlerts()
      await fetchAlerts(5, 'preview')
    } catch (err) {
      error.value = err instanceof Error ? err.message : '保存事件提醒失败'
    } finally {
      submitting.value = false
    }
  }

  function resetForm() {
    Object.assign(form, createEmptyForm())
    editingAlertId.value = ''
  }

  function startEdit(item: AlertItem) {
    editingAlertId.value = item.id
    Object.assign(form, {
      event_time: formatEventTimeForInput(item.event_time),
      event_title: item.event_title,
      potential_risk: item.potential_risk,
      stock_name: item.stock_name,
      stock_code: item.stock_code,
      concept_name: item.concept_name,
      severity: item.severity || 'medium',
      status: item.status || 'pending',
      notes: item.notes,
      created_by: item.updated_by || item.created_by || 'admin'
    })
  }

  async function removeAlert(item: AlertItem) {
    submitting.value = true
    error.value = ''
    successMessage.value = ''

    try {
      const response = await deleteAlert(item.id, form.created_by || item.updated_by || item.created_by)
      const result = response.data as DeleteAlertResponse
      if (!result.success) {
        throw new Error(result.error || '删除事件提醒失败')
      }

      if (editingAlertId.value === item.id) {
        resetForm()
      }

      successMessage.value = '事件提醒已删除'
      await fetchAlerts()
      await fetchAlerts(5, 'preview')
    } catch (err) {
      error.value = err instanceof Error ? err.message : '删除事件提醒失败'
    } finally {
      submitting.value = false
    }
  }

  return {
    loading,
    submitting,
    error,
    successMessage,
    editingAlertId,
    items,
    previewItems,
    totalCount,
    form,
    hasItems,
    hasPreviewItems,
    highRiskCount,
    isEditing,
    fetchAlerts,
    submitAlert,
    resetForm,
    startEdit,
    removeAlert
  }
})
