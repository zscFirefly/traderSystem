<template>
  <div class="page-stack">
    <PageSection title="事件提醒" description="支持录入时间节点、事件、潜在风险，并保留常见后台审计字段。当前数据先落 CSV。">
      <div class="two-column alerts-grid">
        <div class="card-block">
          <div class="result-header">
            <h4 class="panel-title">{{ alertsStore.isEditing ? '编辑提醒' : '提醒录入' }}</h4>
            <span v-if="alertsStore.isEditing" class="result-note">正在编辑现有提醒，保存后会更新 CSV 记录。</span>
          </div>
          <div class="form-grid">
            <div class="field-row">
              <label class="field-label" for="event-time">时间节点 <span class="required-mark">*</span></label>
              <input id="event-time" v-model="alertsStore.form.event_time" class="field-input" type="datetime-local" />
            </div>

            <div class="field-row">
              <label class="field-label" for="event-title">事件 <span class="required-mark">*</span></label>
              <input id="event-title" v-model="alertsStore.form.event_title" class="field-input" placeholder="例如：年报披露窗口" />
            </div>

            <div class="field-row field-row-full">
              <label class="field-label" for="potential-risk">潜在风险 <span class="required-mark">*</span></label>
              <textarea
                id="potential-risk"
                v-model="alertsStore.form.potential_risk"
                class="field-textarea"
                placeholder="例如：业绩不及预期、公告延期、监管关注"
              />
            </div>

            <div class="field-row">
              <label class="field-label" for="stock-name">股票名称</label>
              <input id="stock-name" v-model="alertsStore.form.stock_name" class="field-input" placeholder="可选" />
            </div>

            <div class="field-row">
              <label class="field-label" for="stock-code">股票代码</label>
              <input id="stock-code" v-model="alertsStore.form.stock_code" class="field-input" placeholder="可选" />
            </div>

            <div class="field-row">
              <label class="field-label" for="concept-name">关联概念</label>
              <input id="concept-name" v-model="alertsStore.form.concept_name" class="field-input" placeholder="可选" />
            </div>

            <div class="field-row">
              <label class="field-label" for="severity">风险等级</label>
              <select id="severity" v-model="alertsStore.form.severity" class="field-input">
                <option value="low">低</option>
                <option value="medium">中</option>
                <option value="high">高</option>
              </select>
            </div>

            <div class="field-row">
              <label class="field-label" for="status">状态</label>
              <select id="status" v-model="alertsStore.form.status" class="field-input">
                <option value="pending">待跟踪</option>
                <option value="tracking">跟踪中</option>
                <option value="closed">已关闭</option>
              </select>
            </div>

            <div class="field-row">
              <label class="field-label" for="created-by">创建人</label>
              <input id="created-by" v-model="alertsStore.form.created_by" class="field-input" placeholder="例如：admin" />
            </div>

            <div class="field-row field-row-full">
              <label class="field-label" for="notes">备注</label>
              <textarea id="notes" v-model="alertsStore.form.notes" class="field-textarea" placeholder="补充说明、跟踪计划、审计备注" />
            </div>
          </div>

          <div class="button-row">
            <button class="primary-button" :disabled="alertsStore.submitting" @click="submitAlert">
              {{ alertsStore.submitting ? '保存中...' : alertsStore.isEditing ? '保存修改' : '保存提醒' }}
            </button>
            <button class="ghost-button" :disabled="alertsStore.submitting" @click="alertsStore.resetForm">
              {{ alertsStore.isEditing ? '取消编辑' : '重置' }}
            </button>
          </div>

          <p v-if="alertsStore.error" class="error-text">{{ alertsStore.error }}</p>
          <p v-else-if="alertsStore.successMessage" class="success-text">{{ alertsStore.successMessage }}</p>
        </div>

        <div class="card-block">
          <h4 class="panel-title">提醒摘要</h4>
          <div class="summary-stack">
            <MetricCard label="总提醒数" :value="String(alertsStore.totalCount)" note="CSV 中的有效记录" />
            <MetricCard label="高风险提醒" :value="String(alertsStore.highRiskCount)" note="severity = high" />
            <MetricCard
              label="最新录入"
              :value="alertsStore.items[0]?.event_title || '--'"
              :note="alertsStore.items[0]?.event_time || '暂无记录'"
            />
          </div>
        </div>
      </div>

      <div class="card-block">
        <div class="result-header">
          <h4 class="panel-title">提醒列表</h4>
          <span class="result-note">包含时间节点、风险等级、状态和常见审计字段。</span>
        </div>

        <div v-if="alertsStore.loading" class="empty-hint">正在加载提醒列表...</div>
        <div v-else-if="alertsStore.hasItems" class="alert-list">
          <article
            v-for="item in alertsStore.items"
            :key="item.id"
            class="alert-card"
            @click="openDetail(item)"
          >
            <div class="alert-main">
              <div>
                <p class="alert-time">{{ item.event_time }}</p>
                <h5 class="alert-title">{{ item.event_title }}</h5>
              </div>
              <div class="alert-actions">
                <span class="severity-chip" :class="`severity-${item.severity}`">{{ severityLabel(item.severity) }}</span>
                <span class="status-chip">{{ statusLabel(item.status) }}</span>
                <button class="ghost-button small-button" @click.stop="editAlert(item)">编辑</button>
                <button class="ghost-button small-button danger-button" @click.stop="deleteAlert(item)">删除</button>
              </div>
            </div>

            <p class="alert-risk">{{ item.potential_risk }}</p>

            <div class="alert-meta">
              <span class="meta-chip">股票 {{ item.stock_name || '--' }} {{ item.stock_code || '' }}</span>
              <span class="meta-chip">概念 {{ item.concept_name || '--' }}</span>
              <span class="meta-chip">创建人 {{ item.created_by || '--' }}</span>
              <span class="meta-chip">创建时间 {{ item.created_at || '--' }}</span>
            </div>
          </article>
        </div>
        <div v-else class="empty-hint">暂无提醒记录。先录入一条事件提醒。</div>
      </div>
    </PageSection>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

import MetricCard from '@/components/common/MetricCard.vue'
import PageSection from '@/components/common/PageSection.vue'
import { useAppStore } from '@/stores/app'
import { useAlertsStore } from '@/stores/alerts'
import type { AlertItem } from '@/types/alert'

const appStore = useAppStore()
const alertsStore = useAlertsStore()

onMounted(async () => {
  await alertsStore.fetchAlerts()
})

async function submitAlert() {
  await alertsStore.submitAlert()
}

function editAlert(item: AlertItem) {
  alertsStore.startEdit(item)
}

async function deleteAlert(item: AlertItem) {
  const confirmed = window.confirm(`确认删除事件提醒「${item.event_title}」吗？`)
  if (!confirmed) {
    return
  }

  await alertsStore.removeAlert(item)
}

function openDetail(item: AlertItem) {
  appStore.openDrawer(`${item.event_title} 详情`, item)
}

function severityLabel(value: string) {
  if (value === 'high') return '高风险'
  if (value === 'low') return '低风险'
  return '中风险'
}

function statusLabel(value: string) {
  if (value === 'tracking') return '跟踪中'
  if (value === 'closed') return '已关闭'
  return '待跟踪'
}
</script>

<style scoped>
.alerts-grid {
  align-items: start;
}

.panel-title {
  margin: 0 0 16px;
  font-size: 18px;
  color: var(--text);
}

.field-label,
.result-note,
.empty-hint {
  color: var(--text-soft);
}

.field-label {
  font-size: 13px;
  margin-bottom: 6px;
}

.required-mark {
  color: #c62828;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px 16px;
}

.field-row {
  display: flex;
  flex-direction: column;
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

.button-row,
.result-header,
.alert-main,
.alert-meta,
.alert-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.button-row {
  margin-top: 16px;
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

.summary-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.result-header {
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 14px;
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.alert-card {
  padding: 18px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: linear-gradient(180deg, #fff 0%, #f9fbff 100%);
  cursor: pointer;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.alert-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}

.alert-main {
  justify-content: space-between;
  align-items: flex-start;
}

.alert-actions {
  align-items: center;
}

.alert-time,
.alert-risk {
  margin: 0;
  color: var(--text-soft);
}

.alert-title {
  margin: 4px 0 0;
  color: var(--text);
}

.alert-risk {
  margin-top: 12px;
}

.alert-meta {
  margin-top: 14px;
}

.meta-chip,
.severity-chip,
.status-chip {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 13px;
}

.small-button {
  padding: 6px 10px;
  font-size: 13px;
}

.danger-button {
  color: #b3261e;
  border-color: rgba(179, 38, 30, 0.24);
}

.meta-chip,
.status-chip {
  background: var(--surface-soft);
  color: var(--text);
}

.severity-low {
  background: rgba(31, 111, 235, 0.12);
  color: #1f6feb;
}

.severity-medium {
  background: rgba(224, 147, 37, 0.14);
  color: #9a5d00;
}

.severity-high {
  background: rgba(194, 59, 49, 0.12);
  color: #b3261e;
}

.error-text {
  margin: 12px 0 0;
  color: #c62828;
}

.success-text {
  margin: 12px 0 0;
  color: #2e7d32;
}

@media (max-width: 900px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .result-header,
  .alert-main {
    flex-direction: column;
  }
}
</style>
