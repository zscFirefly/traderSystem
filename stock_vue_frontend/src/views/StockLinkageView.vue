<template>
  <div class="page-stack">
    <PageSection title="股票关联" description="接入现有 Flask API，先跑通股票搜索、关联股票列表和页内相关性分析面板。">
      <div class="card-block">
        <h4 class="panel-title">查询区</h4>
        <div class="search-toolbar">
          <div class="search-field">
            <label class="field-label" for="stock-query">股票名称</label>
            <div class="suggestion-wrap">
              <input
                id="stock-query"
                v-model="stockStore.query"
                class="field-input"
                placeholder="请输入股票名称，如：三六零"
                @input="onQueryInput"
                @keydown.enter.prevent="submitSearch"
              />
              <div v-if="stockStore.suggestions.length > 0" class="suggestion-panel">
                <button
                  v-for="item in stockStore.suggestions"
                  :key="item"
                  type="button"
                  class="suggestion-item"
                  @click="handleSelectSuggestion(item)"
                >
                  {{ item }}
                </button>
              </div>
            </div>
          </div>

          <div class="field-row toolbar-field">
            <label class="field-label">返回数量</label>
            <select v-model.number="stockStore.topk" class="field-input field-select">
              <option :value="5">5</option>
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
            </select>
          </div>

          <label class="checkbox-row toolbar-checkbox">
            <input v-model="stockStore.match300" type="checkbox" />
            <span>仅匹配 30 开头股票</span>
          </label>

          <div class="button-row toolbar-button">
            <button class="primary-button" :disabled="stockStore.loadingRelated" @click="submitSearch">
              {{ stockStore.loadingRelated ? '查询中...' : '查询关联股票' }}
            </button>
          </div>
        </div>

        <div v-if="stockStore.selectedStock" class="search-summary">
          <span class="meta-chip">目标股票 {{ stockStore.selectedStock }}</span>
          <span v-if="stockStore.targetStockCode" class="meta-chip">代码 {{ stockStore.targetStockCode }}</span>
          <span class="meta-chip">关联结果 {{ stockStore.relatedStocks.length }} 只</span>
        </div>

        <p v-if="stockStore.error" class="error-text">{{ stockStore.error }}</p>
      </div>

      <CorrelationPanel
        :preset-stocks="correlationStocks"
        title="相关性分析面板"
        description="默认带上目标股票和当前关联股票列表，分析最近 10 个交易日的 5 分钟收益率相关性。"
      />

      <div class="card-block">
        <div class="result-header">
          <h4 class="panel-title">关联股票结果</h4>
          <span class="result-note">点击任意结果可在右侧详情抽屉查看明细</span>
        </div>

        <div v-if="stockStore.loadingRelated" class="empty-hint">正在加载关联股票结果...</div>
        <div v-else-if="stockStore.hasResults" class="result-list">
          <article
            v-for="(item, index) in stockStore.relatedStocks"
            :key="`${item.stock_code}-${item.stock_name}`"
            class="result-card"
            @click="openDetail(item)"
          >
            <div class="result-card-main">
              <div>
                <p class="result-rank">#{{ index + 1 }}</p>
                <h5 class="result-name">{{ item.stock_name }}</h5>
              </div>
              <span class="result-code">{{ item.stock_code }}</span>
            </div>

            <div class="result-card-side">
              <span class="meta-chip">共现 {{ item.count }} 次</span>
              <span class="meta-chip">{{ item.dates.length }} 个日期</span>
            </div>

            <div class="result-card-middle">
              <p class="meta-label">概念标签</p>
              <div class="tag-list">
                <span v-for="concept in item.concepts.slice(0, 8)" :key="concept" class="tag-chip">{{ concept }}</span>
              </div>
            </div>

            <div class="result-card-dates">
              <p class="meta-label">最近共现日期</p>
              <p class="date-list">{{ item.dates.slice(0, 4).join(' / ') || '暂无数据' }}</p>
            </div>
          </article>
        </div>
        <div v-else class="empty-hint">暂无结果。先输入股票名称并执行一次查询。</div>
      </div>
    </PageSection>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'

import CorrelationPanel from '@/components/business/correlation/CorrelationPanel.vue'
import PageSection from '@/components/common/PageSection.vue'
import { useAppStore } from '@/stores/app'
import { useCorrelationStore } from '@/stores/correlation'
import { useStockStore } from '@/stores/stock'
import type { CorrelationStockInput } from '@/types/correlation'
import type { RelatedStockItem } from '@/types/stock'

const appStore = useAppStore()
const stockStore = useStockStore()
const correlationStore = useCorrelationStore()

let queryTimer: number | undefined

const correlationStocks = computed<CorrelationStockInput[]>(() => {
  const uniqueStocks = new Map<string, CorrelationStockInput>()

  if (stockStore.selectedStock && stockStore.targetStockCode) {
    uniqueStocks.set(stockStore.targetStockCode, {
      stock_code: stockStore.targetStockCode,
      stock_name: stockStore.selectedStock
    })
  }

  for (const item of stockStore.relatedStocks) {
    if (!item.stock_code || uniqueStocks.has(item.stock_code)) {
      continue
    }

    uniqueStocks.set(item.stock_code, {
      stock_code: item.stock_code,
      stock_name: item.stock_name
    })
  }

  return Array.from(uniqueStocks.values())
})

function onQueryInput() {
  if (queryTimer) {
    window.clearTimeout(queryTimer)
  }

  queryTimer = window.setTimeout(() => {
    stockStore.fetchSuggestions(stockStore.query)
  }, 180)
}

function handleSelectSuggestion(stockName: string) {
  stockStore.selectSuggestion(stockName)
  void submitSearch()
}

async function submitSearch() {
  correlationStore.reset()
  await stockStore.fetchRelatedStocks(stockStore.query)
}

function openDetail(item: RelatedStockItem) {
  appStore.openDrawer(`${item.stock_name} 详情`, {
    code: item.stock_code,
    count: item.count,
    concepts: item.concepts,
    dates: item.dates
  })
}

watch(
  () => stockStore.query,
  (value) => {
    if (!value.trim()) {
      stockStore.clearSuggestions()
    }
  }
)
</script>

<style scoped>
.panel-title {
  margin: 0 0 16px;
  font-size: 18px;
  color: var(--text);
}

.field-label,
.meta-label,
.result-note,
.empty-hint {
  color: var(--text-soft);
}

.field-label {
  font-size: 13px;
  margin-bottom: 6px;
}

.search-toolbar {
  display: grid;
  grid-template-columns: minmax(280px, 1.8fr) minmax(120px, 0.6fr) auto auto;
  gap: 16px;
  align-items: end;
}

.search-field {
  min-width: 0;
}

.field-input {
  width: 100%;
  padding: 11px 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #fff;
}

.field-row {
  display: flex;
  flex-direction: column;
}

.field-select {
  max-width: 180px;
}

.checkbox-row {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-soft);
}

.button-row {
  display: flex;
  gap: 12px;
}

.toolbar-field,
.toolbar-button {
  align-self: end;
}

.toolbar-checkbox {
  align-self: center;
  padding-bottom: 10px;
}

.primary-button {
  padding: 11px 16px;
  border: none;
  border-radius: 12px;
  background: var(--primary);
  color: #fff;
  cursor: pointer;
}

.primary-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.suggestion-wrap {
  position: relative;
}

.suggestion-panel {
  position: absolute;
  inset: calc(100% + 6px) 0 auto;
  z-index: 20;
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: var(--shadow);
  overflow: hidden;
}

.suggestion-item {
  padding: 12px 14px;
  border: none;
  border-bottom: 1px solid var(--border);
  background: #fff;
  text-align: left;
  cursor: pointer;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:hover {
  background: var(--surface-soft);
}

.search-summary,
.result-header,
.result-card-main,
.result-card-side {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.search-summary,
.result-card-side {
  margin-top: 16px;
}

.result-header {
  justify-content: space-between;
  align-items: flex-start;
}

.result-card-main {
  align-items: center;
  min-width: 220px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.meta-chip {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 13px;
  background: var(--surface-soft);
  color: var(--text);
}

.tag-chip {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 13px;
  background: rgba(31, 111, 235, 0.12);
  color: var(--primary-deep);
}

.result-name {
  margin: 0;
  color: var(--text);
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.result-card {
  padding: 18px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: linear-gradient(180deg, #fff 0%, #f9fbff 100%);
  cursor: pointer;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
  display: grid;
  grid-template-columns: minmax(220px, 0.8fr) minmax(180px, 0.8fr) minmax(280px, 1.4fr) minmax(240px, 1fr);
  gap: 18px;
  align-items: start;
}

.result-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}

.result-rank,
.result-code,
.date-list {
  margin: 0;
  color: var(--text-soft);
}

.result-meta,
.meta-label {
  margin-top: 0;
}

.result-card-middle,
.result-card-dates {
  min-width: 0;
}

.error-text {
  margin: 12px 0 0;
  color: #c62828;
}

@media (max-width: 900px) {
  .search-toolbar,
  .result-card {
    grid-template-columns: 1fr;
  }

  .result-header {
    flex-direction: column;
  }

  .toolbar-checkbox {
    padding-bottom: 0;
  }
}
</style>
