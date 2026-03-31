import { computed, reactive, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  createCorrelationPreset,
  deleteCorrelationPreset,
  getCorrelationPresets,
  updateCorrelationPreset
} from '@/services/modules/correlation'
import type {
  CorrelationPresetItem,
  CorrelationPresetListResponse,
  CorrelationPresetMutationResponse,
  CorrelationPresetPayload,
  CorrelationStockInput
} from '@/types/correlation'

function createEmptyForm() {
  return {
    name: '',
    description: '',
    is_pinned: false,
    created_by: 'admin'
  }
}

export const useCorrelationPresetsStore = defineStore('correlationPresets', () => {
  const loading = ref(false)
  const submitting = ref(false)
  const error = ref('')
  const successMessage = ref('')
  const editingPresetId = ref('')
  const items = ref<CorrelationPresetItem[]>([])
  const form = reactive(createEmptyForm())

  const hasItems = computed(() => items.value.length > 0)
  const isEditing = computed(() => Boolean(editingPresetId.value))

  async function fetchPresets(limit?: number) {
    loading.value = true
    error.value = ''
    try {
      const response = await getCorrelationPresets(limit)
      const payload = response.data as CorrelationPresetListResponse
      if (!payload.success) {
        throw new Error(payload.error || '加载相关性方案失败')
      }
      items.value = payload.results ?? []
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载相关性方案失败'
      items.value = []
    } finally {
      loading.value = false
    }
  }

  async function submitPreset(stocks: CorrelationStockInput[], tradingDays: number, period: string) {
    submitting.value = true
    error.value = ''
    successMessage.value = ''
    try {
      const payload: CorrelationPresetPayload = {
        name: form.name,
        description: form.description,
        stocks,
        trading_days: tradingDays,
        period,
        include_heatmaps: false,
        is_pinned: form.is_pinned,
        created_by: form.created_by,
        updated_by: form.created_by
      }

      const response = editingPresetId.value
        ? await updateCorrelationPreset(editingPresetId.value, payload)
        : await createCorrelationPreset(payload)

      const result = response.data as CorrelationPresetMutationResponse
      if (!result.success || !result.item) {
        throw new Error(result.error || '保存相关性方案失败')
      }

      successMessage.value = editingPresetId.value ? '相关性方案已更新' : '相关性方案已保存'
      resetForm()
      await fetchPresets()
      return result.item
    } catch (err) {
      error.value = err instanceof Error ? err.message : '保存相关性方案失败'
      return null
    } finally {
      submitting.value = false
    }
  }

  function resetForm() {
    Object.assign(form, createEmptyForm())
    editingPresetId.value = ''
  }

  function startEdit(item: CorrelationPresetItem) {
    editingPresetId.value = item.id
    Object.assign(form, {
      name: item.name,
      description: item.description,
      is_pinned: item.is_pinned,
      created_by: item.updated_by || item.created_by || 'admin'
    })
  }

  async function removePreset(item: CorrelationPresetItem) {
    submitting.value = true
    error.value = ''
    successMessage.value = ''
    try {
      const response = await deleteCorrelationPreset(item.id, form.created_by || item.updated_by || item.created_by)
      const result = response.data as CorrelationPresetMutationResponse
      if (!result.success) {
        throw new Error(result.error || '删除相关性方案失败')
      }

      if (editingPresetId.value === item.id) {
        resetForm()
      }

      successMessage.value = '相关性方案已删除'
      await fetchPresets()
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '删除相关性方案失败'
      return false
    } finally {
      submitting.value = false
    }
  }

  return {
    loading,
    submitting,
    error,
    successMessage,
    editingPresetId,
    items,
    form,
    hasItems,
    isEditing,
    fetchPresets,
    submitPreset,
    resetForm,
    startEdit,
    removePreset
  }
})
