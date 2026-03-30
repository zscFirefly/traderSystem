<template>
  <div class="page-stack">
    <PageSection title="交易纪律" description="开仓、加仓、止损和禁做规则放在首页，开盘前先过一遍。">
      <div v-if="disciplineStore.loadingRules" class="dashboard-empty">正在加载交易纪律...</div>
      <div v-else-if="disciplineStore.dashboardRules.length" class="dashboard-card-list">
        <article
          v-for="item in disciplineStore.dashboardRules"
          :key="item.id"
          class="dashboard-card"
          @click="openRuleDetail(item)"
        >
          <div class="dashboard-card-header">
            <div>
              <p class="dashboard-subtle">{{ item.rule_type }}</p>
              <h4 class="dashboard-title">{{ item.rule_title }}</h4>
            </div>
            <div class="chip-group">
              <span class="severity-chip" :class="`priority-${item.priority}`">{{ priorityLabel(item.priority) }}</span>
              <span v-if="item.strong_reminder === '1'" class="severity-chip severity-high">强提醒</span>
            </div>
          </div>
          <p class="dashboard-body">{{ item.rule_content }}</p>
          <div class="dashboard-meta">
            <span class="meta-chip">状态 {{ statusLabel(item.status) }}</span>
            <span class="meta-chip">更新 {{ item.updated_at || item.created_at }}</span>
          </div>
        </article>
      </div>
      <div v-else class="dashboard-empty">暂无交易纪律。去“交易纪律”模块先录入规则。</div>
    </PageSection>

    <PageSection title="血泪教训" description="把最容易重复犯的错误放在首页，时刻提醒自己不要再犯。">
      <div v-if="disciplineStore.loadingLessons" class="dashboard-empty">正在加载血泪教训...</div>
      <div v-else-if="disciplineStore.dashboardLessons.length" class="dashboard-card-list">
        <article
          v-for="item in disciplineStore.dashboardLessons"
          :key="item.id"
          class="dashboard-card"
          @click="openLessonDetail(item)"
        >
          <div class="dashboard-card-header">
            <div>
              <p class="dashboard-subtle">{{ item.lesson_time }}</p>
              <h4 class="dashboard-title">{{ item.mistake_action }}</h4>
            </div>
            <span class="severity-chip" :class="`severity-${item.severity}`">{{ severityLabel(item.severity) }}</span>
          </div>
          <p class="dashboard-body">{{ item.actual_outcome }}</p>
          <div class="dashboard-meta">
            <span class="meta-chip">标的 {{ item.target_name || '--' }} {{ item.target_code || '' }}</span>
            <span class="meta-chip">关联纪律 {{ item.linked_rule || '--' }}</span>
          </div>
        </article>
      </div>
      <div v-else class="dashboard-empty">暂无首页展示的血泪教训。去“交易纪律”模块先录入一条记录。</div>
    </PageSection>

    <PageSection title="事件提醒" description="保留最近需要关注的事件提醒，方便和交易纪律一起交叉检查。">
      <div v-if="alertsStore.loading" class="dashboard-empty">正在加载事件提醒...</div>
      <div v-else-if="alertsStore.hasPreviewItems" class="dashboard-card-list">
        <article
          v-for="item in alertsStore.previewItems"
          :key="item.id"
          class="dashboard-card"
          @click="openAlertDetail(item)"
        >
          <div class="dashboard-card-header">
            <div>
              <p class="dashboard-subtle">{{ item.event_time }}</p>
              <h4 class="dashboard-title">{{ item.event_title }}</h4>
            </div>
            <span class="severity-chip" :class="`severity-${item.severity}`">{{ alertSeverityLabel(item.severity) }}</span>
          </div>
          <p class="dashboard-body">{{ item.potential_risk }}</p>
          <div class="dashboard-meta">
            <span class="meta-chip">股票 {{ item.stock_name || '--' }} {{ item.stock_code || '' }}</span>
            <span class="meta-chip">概念 {{ item.concept_name || '--' }}</span>
            <span class="meta-chip">状态 {{ alertStatusLabel(item.status) }}</span>
          </div>
        </article>
      </div>
      <div v-else class="dashboard-empty">暂无事件提醒。去“事件提醒”模块先录入一条记录。</div>
    </PageSection>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

import PageSection from '@/components/common/PageSection.vue'
import { useAppStore } from '@/stores/app'
import { useAlertsStore } from '@/stores/alerts'
import { useDisciplineStore } from '@/stores/discipline'
import type { AlertItem } from '@/types/alert'
import type { DisciplineLessonItem, DisciplineRuleItem } from '@/types/discipline'

const appStore = useAppStore()
const alertsStore = useAlertsStore()
const disciplineStore = useDisciplineStore()

onMounted(async () => {
  await disciplineStore.fetchRules()
  await disciplineStore.fetchRules(5, 'dashboard')
  await disciplineStore.fetchLessons()
  await disciplineStore.fetchLessons(5, 'dashboard')
  await alertsStore.fetchAlerts(5, 'preview')
})

function openRuleDetail(item: DisciplineRuleItem) {
  appStore.openDrawer(`${item.rule_title} 详情`, item)
}

function openLessonDetail(item: DisciplineLessonItem) {
  appStore.openDrawer(`血泪教训详情`, item)
}

function openAlertDetail(item: AlertItem) {
  appStore.openDrawer(`${item.event_title} 详情`, item)
}

function priorityLabel(value: string) {
  if (value === 'high') return '高优先级'
  if (value === 'low') return '低优先级'
  return '中优先级'
}

function severityLabel(value: string) {
  if (value === 'high') return '高严重'
  if (value === 'low') return '低严重'
  return '中严重'
}

function alertSeverityLabel(value: string) {
  if (value === 'high') return '高风险'
  if (value === 'low') return '低风险'
  return '中风险'
}

function statusLabel(value: string) {
  if (value === 'inactive') return '停用'
  return '启用'
}

function alertStatusLabel(value: string) {
  if (value === 'tracking') return '跟踪中'
  if (value === 'closed') return '已关闭'
  return '待跟踪'
}
</script>

<style scoped>
.dashboard-empty {
  color: var(--text-soft);
}

.dashboard-card-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.dashboard-card {
  padding: 18px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: linear-gradient(180deg, #fff 0%, #f9fbff 100%);
  cursor: pointer;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.dashboard-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}

.dashboard-card-header,
.dashboard-meta,
.chip-group {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.dashboard-subtle,
.dashboard-body {
  margin: 0;
  color: var(--text-soft);
}

.dashboard-title {
  margin: 4px 0 0;
  color: var(--text);
}

.dashboard-body {
  margin-top: 12px;
}

.dashboard-meta {
  margin-top: 14px;
}

.chip-group {
  justify-content: flex-end;
}

.meta-chip,
.severity-chip {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 13px;
}

.meta-chip {
  background: var(--surface-soft);
  color: var(--text);
}

.priority-low {
  background: rgba(31, 111, 235, 0.12);
  color: #1f6feb;
}

.priority-medium {
  background: rgba(224, 147, 37, 0.14);
  color: #9a5d00;
}

.priority-high,
.severity-high {
  background: rgba(194, 59, 49, 0.12);
  color: #b3261e;
}

.severity-medium {
  background: rgba(224, 147, 37, 0.14);
  color: #9a5d00;
}

.severity-low {
  background: rgba(31, 111, 235, 0.12);
  color: #1f6feb;
}

@media (max-width: 900px) {
  .dashboard-card-header,
  .dashboard-meta {
    flex-direction: column;
  }

  .chip-group {
    justify-content: flex-start;
  }
}
</style>
