<template>
  <div class="page-stack">
    <PageSection title="相关性分析" description="先跑分析，结果出来后再把当前股票池和参数保存成可复用方案。">
      <div class="page-stack">
        <CorrelationPanel
          editable
          title="独立相关性分析"
          description="手动维护股票池、交易日数和分钟周期，适合单独比较一组标的。"
          :stock-text="stockText"
          @update:stock-text="stockText = $event"
        />

        <div v-if="correlationStore.hasData" class="action-bar">
          <button class="primary-button" @click="openCreateModal">保存方案</button>
          <span class="action-note">
            当前参数：{{ parsedStocks.length }} 只股票，{{ correlationStore.tradingDays }} 个交易日，{{ correlationStore.period }} 分钟线
          </span>
        </div>

        <div class="card-block">
          <div class="result-header">
            <h4 class="panel-title">已保存方案</h4>
            <span class="result-note">点击“加载”会自动回填股票池、交易日数和分钟周期。</span>
          </div>

          <div v-if="presetsStore.loading" class="empty-hint">正在加载方案列表...</div>
          <div v-else-if="presetsStore.hasItems" class="preset-list">
            <article
              v-for="item in presetsStore.items"
              :key="item.id"
              class="preset-card"
              :class="{ 'preset-card-active': item.id === selectedPresetId }"
              @click="selectedPresetId = item.id"
            >
              <div class="preset-header">
                <div>
                  <h5 class="preset-title">{{ item.name }}</h5>
                  <p v-if="item.description" class="preset-description">{{ item.description }}</p>
                </div>
                <div class="action-row">
                  <span v-if="item.is_pinned" class="meta-chip">置顶</span>
                  <button class="ghost-button small-button" @click.stop="loadPreset(item)">加载</button>
                  <button class="ghost-button small-button" @click.stop="openEditModal(item)">编辑</button>
                  <button class="ghost-button small-button danger-button" @click.stop="deletePreset(item)">删除</button>
                </div>
              </div>
              <div class="meta-row">
                <span class="meta-chip">股票 {{ item.stocks.length }} 只</span>
                <span class="meta-chip">{{ item.trading_days }} 个交易日</span>
                <span class="meta-chip">{{ item.period }} 分钟线</span>
                <span class="meta-chip">更新 {{ item.updated_at }}</span>
              </div>
            </article>
          </div>
          <div v-else class="empty-hint">暂无已保存方案。先跑出一组结果，再点击“保存方案”。</div>
        </div>
      </div>
    </PageSection>
  </div>

  <div v-if="saveModalOpen" class="preset-modal-overlay" @click.self="closeModal">
    <div class="preset-modal-card">
      <div class="result-header">
        <h4 class="panel-title">{{ presetsStore.isEditing ? '编辑方案' : '保存方案' }}</h4>
        <button class="ghost-button small-button" @click="closeModal">关闭</button>
      </div>

      <div class="form-grid">
        <div class="field-row">
          <label class="field-label" for="preset-name">方案名称</label>
          <input
            id="preset-name"
            v-model="presetsStore.form.name"
            class="field-input"
            placeholder="例如：机器人链核心票 10日5分钟"
          />
        </div>

        <div class="field-row field-row-full">
          <label class="field-label" for="preset-description">方案说明</label>
          <textarea
            id="preset-description"
            v-model="presetsStore.form.description"
            class="field-textarea"
            placeholder="补充说明这组股票池的用途，例如：早盘联动观察"
          />
        </div>
      </div>

      <div class="meta-row">
        <span class="meta-chip">股票 {{ parsedStocks.length }} 只</span>
        <span class="meta-chip">最近 {{ correlationStore.tradingDays }} 个交易日</span>
        <span class="meta-chip">{{ correlationStore.period }} 分钟线</span>
      </div>

      <div class="button-row">
        <button class="primary-button" :disabled="!canSavePreset || presetsStore.submitting" @click="savePreset">
          {{
            presetsStore.submitting
              ? '保存中...'
              : presetsStore.isEditing
                ? '保存修改'
                : '保存方案'
          }}
        </button>
        <button class="ghost-button" :disabled="presetsStore.submitting" @click="closeModal">取消</button>
      </div>

      <p v-if="localPresetError" class="error-text">{{ localPresetError }}</p>
      <p v-else-if="presetsStore.error" class="error-text">{{ presetsStore.error }}</p>
      <p v-else-if="presetsStore.successMessage" class="success-text">{{ presetsStore.successMessage }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import CorrelationPanel from '@/components/business/correlation/CorrelationPanel.vue'
import PageSection from '@/components/common/PageSection.vue'
import { useCorrelationPresetsStore } from '@/stores/correlationPresets'
import { useCorrelationStore } from '@/stores/correlation'
import type { CorrelationPresetItem, CorrelationStockInput } from '@/types/correlation'

const correlationStore = useCorrelationStore()
const presetsStore = useCorrelationPresetsStore()
const stockText = ref('')
const selectedPresetId = ref('')
const saveModalOpen = ref(false)
const localPresetError = ref('')

const parsedStocks = computed<CorrelationStockInput[]>(() => {
  const uniqueStocks = new Map<string, CorrelationStockInput>()
  const lines = stockText.value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)

  for (const line of lines) {
    const segments = line
      .split(/[:,，：]/)
      .map((item) => item.trim())
      .filter(Boolean)

    if (segments.length < 2) {
      continue
    }

    const [stock_code, stock_name] = segments
    if (!stock_code || !stock_name || uniqueStocks.has(stock_code)) {
      continue
    }

    uniqueStocks.set(stock_code, { stock_code, stock_name })
  }

  return Array.from(uniqueStocks.values())
})

const canSavePreset = computed(() => Boolean(presetsStore.form.name.trim()) && parsedStocks.value.length >= 1)

onMounted(async () => {
  correlationStore.reset()
  await presetsStore.fetchPresets()
})

function formatStocks(stocks: CorrelationStockInput[]) {
  return stocks.map((item) => `${item.stock_code}:${item.stock_name}`).join('\n')
}

function loadPreset(item: CorrelationPresetItem) {
  selectedPresetId.value = item.id
  stockText.value = formatStocks(item.stocks)
  correlationStore.tradingDays = item.trading_days
  correlationStore.period = item.period
  correlationStore.reset()
  localPresetError.value = ''
  presetsStore.successMessage = ''
}

function openCreateModal() {
  presetsStore.resetForm()
  localPresetError.value = ''
  saveModalOpen.value = true
}

function openEditModal(item: CorrelationPresetItem) {
  loadPreset(item)
  presetsStore.startEdit(item)
  localPresetError.value = ''
  saveModalOpen.value = true
}

function closeModal() {
  saveModalOpen.value = false
  localPresetError.value = ''
  presetsStore.resetForm()
}

async function deletePreset(item: CorrelationPresetItem) {
  const confirmed = window.confirm(`确认删除相关性方案「${item.name}」吗？`)
  if (!confirmed) {
    return
  }

  const deleted = await presetsStore.removePreset(item)
  if (deleted && selectedPresetId.value === item.id) {
    selectedPresetId.value = ''
  }
}

async function savePreset() {
  localPresetError.value = ''

  if (!presetsStore.form.name.trim()) {
    localPresetError.value = '请填写方案名称'
    return
  }

  if (!parsedStocks.value.length) {
    localPresetError.value = '请至少填写一只股票后再保存方案'
    return
  }

  const saved = await presetsStore.submitPreset(
    parsedStocks.value,
    correlationStore.tradingDays,
    correlationStore.period
  )
  if (saved) {
    selectedPresetId.value = saved.id
    saveModalOpen.value = false
  }
}
</script>

<style scoped>
.panel-title,
.preset-title {
  margin: 0;
  color: var(--text);
}

.preset-title {
  font-size: 16px;
}

.action-bar,
.result-header,
.button-row,
.preset-header,
.meta-row,
.action-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-bar,
.result-header,
.preset-header {
  justify-content: space-between;
  align-items: center;
}

.action-note,
.result-note,
.field-label,
.empty-hint,
.preset-description {
  color: var(--text-soft);
}

.preset-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.preset-card {
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: linear-gradient(180deg, #fff 0%, #f9fbff 100%);
  cursor: pointer;
}

.preset-card-active {
  border-color: var(--primary);
  box-shadow: 0 10px 24px rgba(31, 111, 235, 0.12);
}

.meta-row {
  margin-top: 12px;
}

.meta-chip {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 13px;
  background: var(--surface-soft);
  color: var(--text);
}

.primary-button {
  padding: 11px 16px;
  border: none;
  border-radius: 12px;
  background: var(--primary);
  color: #fff;
  cursor: pointer;
}

.primary-button:disabled,
.ghost-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.small-button {
  padding: 8px 12px;
}

.danger-button {
  color: #b3261e;
}

.preset-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 210;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(19, 32, 51, 0.42);
  backdrop-filter: blur(4px);
}

.preset-modal-card {
  width: min(640px, 100%);
  padding: 20px;
  border-radius: 20px;
  background: #fff;
  box-shadow: 0 18px 48px rgba(19, 32, 51, 0.18);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px 16px;
  margin-top: 16px;
}

.field-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-row-full {
  grid-column: 1 / -1;
}

.field-input,
.field-textarea {
  width: 100%;
  padding: 11px 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #fff;
  font: inherit;
}

.field-textarea {
  min-height: 96px;
  resize: vertical;
}

.button-row {
  margin-top: 16px;
}

.error-text {
  margin: 16px 0 0;
  color: #c62828;
}

.success-text {
  margin: 16px 0 0;
  color: #2e7d32;
}

@media (max-width: 900px) {
  .action-bar,
  .result-header,
  .preset-header {
    align-items: stretch;
    flex-direction: column;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
