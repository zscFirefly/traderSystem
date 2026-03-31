<template>
  <div class="card-block correlation-panel-block">
    <div class="panel-header">
      <div>
        <h4 class="panel-title">{{ title }}</h4>
        <p v-if="description" class="panel-note">{{ description }}</p>
      </div>
      <div class="action-row">
        <button class="secondary-button" :disabled="!canAnalyze || correlationStore.loading" @click="togglePanel">
          {{ correlationStore.expanded ? '收起相关性分析' : '展开相关性分析' }}
        </button>
        <button
          v-if="correlationStore.expanded"
          class="ghost-button inline-button"
          :disabled="!canAnalyze || correlationStore.loading"
          @click="refreshCorrelation"
        >
          {{ correlationStore.loading ? '分析中...' : '刷新分析' }}
        </button>
      </div>
    </div>

    <div v-if="editable" class="editor-stack">
      <label class="field-label" for="correlation-stock-pool">股票池</label>
      <textarea
        id="correlation-stock-pool"
        v-model="stockTextModel"
        class="field-textarea"
        placeholder="每行一只，格式：601127:赛力斯"
      />
      <div class="parameter-grid">
        <div class="field-row">
          <label class="field-label" for="correlation-trading-days">交易日数</label>
          <input
            id="correlation-trading-days"
            v-model.number="correlationStore.tradingDays"
            class="field-input"
            type="number"
            min="1"
            max="120"
          />
        </div>
        <div class="field-row">
          <label class="field-label" for="correlation-period">分钟周期</label>
          <select id="correlation-period" v-model="correlationStore.period" class="field-input">
            <option value="5">5 分钟</option>
            <option value="15">15 分钟</option>
            <option value="30">30 分钟</option>
            <option value="60">60 分钟</option>
          </select>
        </div>
      </div>
      <p class="panel-note">支持 `代码:名称` 或 `代码,名称`，至少填写两只股票。</p>
      <p v-if="parseError" class="error-text">{{ parseError }}</p>
    </div>

    <div v-if="!analysisStocks.length" class="empty-hint">
      {{ emptyMessage }}
    </div>

    <template v-else>
      <div class="correlation-meta">
        <div class="meta-group">
          <span class="meta-chip">股票池 {{ analysisStocks.length }} 只</span>
          <span class="meta-chip">最近 {{ correlationStore.tradingDays }} 个交易日</span>
          <span class="meta-chip">{{ correlationStore.period }} 分钟线</span>
          <span v-if="correlationStore.returnsCount > 0" class="meta-chip">样本点 {{ correlationStore.returnsCount }}</span>
          <span v-if="correlationStore.failedStocks?.length" class="meta-chip">失败 {{ correlationStore.failedStocks.length }} 只</span>
        </div>
        <p v-if="correlationStore.timeRange" class="date-list">
          {{ correlationStore.timeRange.start_date }} 至 {{ correlationStore.timeRange.end_date }}
        </p>
      </div>

      <p v-if="correlationStore.error" class="error-text">{{ correlationStore.error }}</p>
      <p v-if="correlationStore.failedStocks?.length" class="panel-note">
        未成功获取数据：
        {{ correlationStore.failedStocks.map((item) => `${item.name}(${item.symbol})`).join('、') }}
      </p>
      <div v-else-if="correlationStore.loading" class="empty-hint">正在拉取分钟数据并生成相关性热力图，可能需要 1 到 3 分钟，请稍候...</div>
      <div v-else-if="correlationStore.expanded && correlationStore.hasData" class="analysis-stack">
        <div class="method-switcher">
          <button
            v-for="method in correlationStore.availableMethods"
            :key="method"
            type="button"
            class="method-button"
            :class="{ 'method-button-active': method === correlationStore.activeMethod }"
            @click="setMethod(method)"
          >
            {{ methodLabels[method] }}
          </button>
        </div>

        <div class="view-switcher">
          <button
            type="button"
            class="method-button"
            :class="{ 'method-button-active': heatmapViewMode === 'correlation' }"
            :disabled="!correlationStore.currentMatrix"
            @click="heatmapViewMode = 'correlation'"
          >
            {{ methodLabels[correlationStore.activeMethod] }} 相关性热力图
          </button>
          <button
            type="button"
            class="method-button"
            :class="{ 'method-button-active': heatmapViewMode === 'significance' }"
            :disabled="!correlationStore.significanceMatrix"
            @click="heatmapViewMode = 'significance'"
          >
            显著性热力图
          </button>
        </div>

        <div class="chart-panel">
          <div class="chart-header">
            <div>
              <h5 class="chart-title">{{ displayedChartTitle }}</h5>
              <p class="panel-note">{{ displayedChartNote }}</p>
            </div>
            <button class="ghost-button inline-button" @click="openFullscreen">全屏查看热力图</button>
          </div>
          <MatrixHeatmap
            v-if="displayedMatrix"
            :matrix="displayedMatrix"
            :min="displayedRange.min"
            :max="displayedRange.max"
            :colors="displayedColors"
            :label-formatter="displayedLabelFormatter"
            :tooltip-formatter="displayedTooltipFormatter"
          />
          <p v-else class="empty-hint">当前视图未返回热力图。</p>
        </div>
      </div>
      <div v-else-if="correlationStore.expanded" class="empty-hint">暂无可展示的相关性结果。</div>
    </template>
  </div>

  <div v-if="fullscreenOpen && displayedMatrix" class="fullscreen-overlay" @click.self="closeFullscreen">
    <div class="fullscreen-card">
      <div class="chart-header fullscreen-header">
        <div>
          <h4 class="panel-title">{{ displayedChartTitle }}</h4>
          <p class="panel-note">{{ displayedChartNote }}</p>
        </div>
        <div class="action-row">
          <button class="ghost-button inline-button" @click="zoomOut">缩小</button>
          <button class="ghost-button inline-button" @click="resetZoom">重置</button>
          <button class="ghost-button inline-button" @click="zoomIn">放大</button>
          <button class="ghost-button inline-button" @click="closeFullscreen">关闭全屏</button>
        </div>
      </div>
      <p class="panel-note fullscreen-scale-note">当前缩放 {{ Math.round(fullscreenScale * 100) }}%</p>
      <MatrixHeatmap
        :matrix="displayedMatrix"
        :min="displayedRange.min"
        :max="displayedRange.max"
        :colors="displayedColors"
        :label-formatter="displayedLabelFormatter"
        :tooltip-formatter="displayedTooltipFormatter"
        :scale="fullscreenScale"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import MatrixHeatmap from '@/components/charts/MatrixHeatmap.vue'
import { useCorrelationStore } from '@/stores/correlation'
import type { CorrelationMethod, CorrelationStockInput } from '@/types/correlation'

interface Props {
  presetStocks?: CorrelationStockInput[]
  title?: string
  description?: string
  editable?: boolean
  stockText?: string
}

const props = withDefaults(defineProps<Props>(), {
  presetStocks: () => [],
  title: '相关性分析面板',
  description: '',
  editable: false,
  stockText: ''
})
const emit = defineEmits<{
  'update:stockText': [value: string]
}>()

const METHOD_LABELS: Record<CorrelationMethod, string> = {
  pearson: 'Pearson',
  spearman: 'Spearman',
  kendall: 'Kendall'
}

const correlationStore = useCorrelationStore()
const internalStockText = ref(props.stockText)
const heatmapViewMode = ref<'correlation' | 'significance'>('correlation')
const fullscreenOpen = ref(false)
const fullscreenScale = ref(1)

const methodLabels = METHOD_LABELS

const stockTextModel = computed({
  get: () => (props.editable ? props.stockText : internalStockText.value),
  set: (value: string) => {
    if (props.editable) {
      emit('update:stockText', value)
      return
    }
    internalStockText.value = value
  }
})

const parsedManualStocks = computed<CorrelationStockInput[]>(() => {
  if (!props.editable) {
    return []
  }

  const uniqueStocks = new Map<string, CorrelationStockInput>()
  const lines = stockTextModel.value
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

const parseError = computed(() => {
  if (!props.editable || !stockTextModel.value.trim()) {
    return ''
  }

  const rawLines = stockTextModel.value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)

  const validLines = parsedManualStocks.value.length
  if (validLines === rawLines.length) {
    return ''
  }

  return '存在无法识别的行，请按“代码:名称”格式填写。'
})

const analysisStocks = computed(() => {
  if (props.editable) {
    return parsedManualStocks.value
  }
  return props.presetStocks
})

const canAnalyze = computed(() => analysisStocks.value.length >= 2)

const emptyMessage = computed(() => {
  if (props.editable) {
    return '先维护股票池，再展开相关性分析。'
  }
  return '当前股票池不足，至少需要两只股票才能进行相关性分析。'
})

const displayedMatrix = computed(() =>
  heatmapViewMode.value === 'significance'
    ? correlationStore.significanceMatrix
    : correlationStore.currentMatrix
)

const displayedChartTitle = computed(() =>
  heatmapViewMode.value === 'significance'
    ? '显著性热力图'
    : `${methodLabels[correlationStore.activeMethod]} 相关性热力图`
)

const displayedChartNote = computed(() =>
  heatmapViewMode.value === 'significance' ? 'p 值矩阵' : '当前方法'
)

const displayedRange = computed(() =>
  heatmapViewMode.value === 'significance' ? { min: 0, max: 1 } : { min: -1, max: 1 }
)

const displayedColors = computed(() =>
  heatmapViewMode.value === 'significance'
    ? ['#fff5f0', '#fddbc7', '#f4a582', '#d6604d', '#b2182b']
    : ['#2f5fa7', '#85aee2', '#f6f8fb', '#f0b2a2', '#c23b31']
)

const displayedLabelFormatter = computed(() =>
  heatmapViewMode.value === 'significance' ? formatSignificanceLabel : formatCorrelationLabel
)

const displayedTooltipFormatter = computed(() =>
  heatmapViewMode.value === 'significance' ? formatSignificanceTooltip : formatCorrelationTooltip
)

async function runCorrelation(force = false) {
  if (!canAnalyze.value) {
    correlationStore.setError('至少需要两只股票才能进行相关性分析')
    return
  }

  await correlationStore.fetchCorrelation(analysisStocks.value, force)
}

async function togglePanel() {
  if (correlationStore.expanded) {
    correlationStore.setExpanded(false)
    fullscreenOpen.value = false
    fullscreenScale.value = 1
    return
  }

  correlationStore.setExpanded(true)
  await runCorrelation()
}

async function refreshCorrelation() {
  await runCorrelation(true)
}

function setMethod(method: CorrelationMethod) {
  correlationStore.setActiveMethod(method)
  heatmapViewMode.value = 'correlation'
}

function formatCorrelationLabel(value: number) {
  return value.toFixed(2)
}

function formatCorrelationTooltip(value: number) {
  return `${value.toFixed(4)}`
}

function formatSignificanceLabel(value: number) {
  return value.toFixed(3)
}

function formatSignificanceTooltip(value: number) {
  return `p = ${value.toFixed(4)}`
}

function openFullscreen() {
  fullscreenScale.value = 1
  fullscreenOpen.value = true
}

function closeFullscreen() {
  fullscreenOpen.value = false
  fullscreenScale.value = 1
}

function zoomIn() {
  fullscreenScale.value = Math.min(2.4, Number((fullscreenScale.value + 0.2).toFixed(1)))
}

function zoomOut() {
  fullscreenScale.value = Math.max(0.6, Number((fullscreenScale.value - 0.2).toFixed(1)))
}

function resetZoom() {
  fullscreenScale.value = 1
}

watch(
  () => props.presetStocks,
  () => {
    if (!props.editable) {
      correlationStore.reset()
      heatmapViewMode.value = 'correlation'
      fullscreenOpen.value = false
      fullscreenScale.value = 1
    }
  },
  { deep: true }
)

watch(
  () => props.stockText,
  (value) => {
    internalStockText.value = value
  }
)

watch(stockTextModel, () => {
  if (props.editable) {
    correlationStore.reset()
    heatmapViewMode.value = 'correlation'
    fullscreenOpen.value = false
    fullscreenScale.value = 1
  }
})

watch(
  () => [correlationStore.tradingDays, correlationStore.period],
  () => {
    if (props.editable) {
      correlationStore.reset()
      heatmapViewMode.value = 'correlation'
      fullscreenOpen.value = false
      fullscreenScale.value = 1
    }
  }
)
</script>

<style scoped>
.correlation-panel-block {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-header,
.chart-header,
.correlation-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.panel-header,
.chart-header {
  align-items: flex-start;
}

.panel-title {
  margin: 0;
  font-size: 18px;
  color: var(--text);
}

.panel-note,
.field-label,
.empty-hint {
  margin: 0;
  color: var(--text-soft);
}

.editor-stack,
.analysis-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.parameter-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.field-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 13px;
}

.field-input,
.field-textarea {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #fff;
  font: inherit;
}

.field-textarea {
  min-height: 112px;
  resize: vertical;
}

.action-row,
.method-switcher,
.view-switcher,
.meta-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.secondary-button,
.method-button {
  padding: 11px 16px;
  border: none;
  border-radius: 12px;
  cursor: pointer;
}

.secondary-button {
  background: var(--primary-deep);
  color: #fff;
}

.inline-button {
  padding: 11px 16px;
}

.secondary-button:disabled,
.inline-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.meta-chip {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 13px;
}

.meta-chip {
  background: var(--surface-soft);
  color: var(--text);
}

.chart-panel {
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: var(--surface-soft);
}

.chart-title {
  margin: 0;
  color: var(--text);
}

.method-button {
  background: #fff;
  color: var(--text-soft);
  border: 1px solid var(--border);
}

.method-button-active {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}

.error-text {
  margin: 0;
  color: #c62828;
}

.date-list {
  margin: 0;
  color: var(--text-soft);
}

.fullscreen-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: stretch;
  justify-content: center;
  padding: 24px;
  background: rgba(19, 32, 51, 0.45);
  backdrop-filter: blur(4px);
}

.fullscreen-card {
  width: min(1400px, 100%);
  height: 100%;
  overflow: auto;
  padding: 20px;
  border-radius: 24px;
  background: #fff;
  box-shadow: 0 18px 48px rgba(19, 32, 51, 0.18);
}

.fullscreen-header {
  margin-bottom: 16px;
}

.fullscreen-scale-note {
  margin-bottom: 12px;
}

@media (max-width: 900px) {
  .parameter-grid,
  .panel-header,
  .chart-header,
  .correlation-meta {
    display: flex;
    flex-direction: column;
  }

  .action-row {
    width: 100%;
  }

  .fullscreen-overlay {
    padding: 12px;
  }
}
</style>
