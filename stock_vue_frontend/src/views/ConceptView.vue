<template>
  <div class="page-stack">
    <PageSection title="概念专题" description="接入现有 Flask API，先跑通概念查询、概念摘要和概念股票列表。">
      <div class="card-block">
        <h4 class="panel-title">概念查询</h4>
        <div class="search-toolbar">
          <div class="search-field">
            <label class="field-label" for="concept-query">概念名称</label>
            <input
              id="concept-query"
              v-model="conceptStore.query"
              class="field-input"
              placeholder="请输入概念名称，如：绿色电力"
              @keydown.enter.prevent="submitSearch"
            />
          </div>

          <div class="field-row toolbar-field">
            <label class="field-label">返回数量</label>
            <select v-model.number="conceptStore.topk" class="field-input field-select">
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="30">30</option>
              <option :value="50">50</option>
            </select>
          </div>

          <div class="field-row toolbar-field">
            <label class="field-label">最小关联频次</label>
            <select v-model.number="conceptStore.minWeight" class="field-input field-select">
              <option :value="1">1</option>
              <option :value="2">2</option>
              <option :value="3">3</option>
              <option :value="5">5</option>
            </select>
          </div>

          <div class="button-row toolbar-button">
            <button class="primary-button" :disabled="conceptStore.loading" @click="submitSearch">
              {{ conceptStore.loading ? '查询中...' : '查询概念' }}
            </button>
          </div>
        </div>

        <p v-if="conceptStore.error" class="error-text">{{ conceptStore.error }}</p>
        <p v-else-if="conceptStore.message" class="empty-hint">{{ conceptStore.message }}</p>
      </div>

      <div class="three-column summary-grid">
        <MetricCard
          label="目标概念"
          :value="conceptStore.selectedConcept || '--'"
          note="当前查询上下文"
        />
        <MetricCard
          label="概念股票数"
          :value="String(conceptStore.totalCount || 0)"
          note="该概念覆盖股票数量"
        />
        <MetricCard
          label="关系图规模"
          :value="graphValue"
          note="节点数 / 边数"
        />
      </div>

      <div class="card-block">
        <div class="result-header">
          <h4 class="panel-title">概念股票列表</h4>
          <span class="result-note">点击任意结果可在右侧详情抽屉查看概念、中心性和关联股票。</span>
        </div>

        <div v-if="conceptStore.loading" class="empty-hint">正在加载概念股票结果...</div>
        <div v-else-if="conceptStore.hasResults" class="result-list">
          <article
            v-for="(item, index) in conceptStore.results"
            :key="`${item.stock_code}-${item.stock_name}`"
            class="result-card"
            @click="openDetail(item)"
          >
            <div class="result-card-main">
              <div>
                <p class="result-rank">#{{ index + 1 }}</p>
                <h5 class="result-name">{{ item.stock_name }}</h5>
              </div>
              <span class="result-code">{{ item.stock_code || '暂无代码' }}</span>
            </div>

            <div class="result-card-side">
              <span class="meta-chip">中心性 {{ item.centrality.toFixed(4) }}</span>
              <span class="meta-chip">关联股 {{ item.related_stocks.length }} 只</span>
            </div>

            <div class="result-card-middle">
              <p class="meta-label">概念标签</p>
              <div class="tag-list">
                <span v-for="concept in item.concepts.slice(0, 8)" :key="concept" class="tag-chip">{{ concept }}</span>
              </div>
            </div>

            <div class="result-card-dates">
              <p class="meta-label">关联股票</p>
              <p class="date-list">{{ item.related_stocks.slice(0, 5).join(' / ') || '暂无数据' }}</p>
            </div>
          </article>
        </div>
        <div v-else class="empty-hint">暂无结果。先输入概念名称并执行一次查询。</div>
      </div>
    </PageSection>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import MetricCard from '@/components/common/MetricCard.vue'
import PageSection from '@/components/common/PageSection.vue'
import { useAppStore } from '@/stores/app'
import { useConceptStore } from '@/stores/concept'
import type { ConceptStockItem } from '@/types/concept'

const appStore = useAppStore()
const conceptStore = useConceptStore()

const graphValue = computed(() => {
  if (!conceptStore.graphStats) {
    return '--'
  }

  return `${conceptStore.graphStats.nodes} / ${conceptStore.graphStats.edges}`
})

async function submitSearch() {
  await conceptStore.fetchConceptStocks(conceptStore.query)
}

function openDetail(item: ConceptStockItem) {
  appStore.openDrawer(`${item.stock_name} 详情`, {
    code: item.stock_code,
    centrality: item.centrality,
    concepts: item.concepts,
    related_stocks: item.related_stocks
  })
}
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
  grid-template-columns: minmax(280px, 1.8fr) minmax(120px, 0.7fr) minmax(140px, 0.8fr) auto;
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

.button-row {
  display: flex;
  gap: 12px;
}

.toolbar-field,
.toolbar-button {
  align-self: end;
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

.summary-grid {
  align-items: stretch;
}

.result-header,
.result-card-main,
.result-card-side {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
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

.meta-label {
  margin: 0 0 8px;
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
}
</style>
