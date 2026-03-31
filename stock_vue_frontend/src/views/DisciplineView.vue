<template>
  <div class="page-stack">
    <PageSection title="交易纪律" description="把交易纪律和血泪教训沉淀成可维护的规则库，首页会持续展示核心提醒。">
      <div class="two-column discipline-grid">
        <div class="card-block">
          <div class="result-header">
            <h4 class="panel-title">{{ disciplineStore.isEditingRule ? '编辑纪律清单' : '纪律清单录入' }}</h4>
            <span v-if="disciplineStore.isEditingRule" class="result-note">正在编辑现有规则，保存后会更新 CSV 记录。</span>
          </div>
          <div class="form-grid">
            <div class="field-row">
              <label class="field-label" for="rule-title">规则标题 <span class="required-mark">*</span></label>
              <input id="rule-title" v-model="disciplineStore.ruleForm.rule_title" class="field-input" placeholder="例如：不追 3 连板后的放量冲高" />
            </div>

            <div class="field-row">
              <label class="field-label" for="rule-type">规则类型</label>
              <select id="rule-type" v-model="disciplineStore.ruleForm.rule_type" class="field-input">
                <option value="开仓">开仓</option>
                <option value="加仓">加仓</option>
                <option value="止损">止损</option>
                <option value="止盈">止盈</option>
                <option value="禁做">禁做</option>
              </select>
            </div>

            <div class="field-row field-row-full">
              <label class="field-label" for="rule-content">规则内容 <span class="required-mark">*</span></label>
              <textarea id="rule-content" v-model="disciplineStore.ruleForm.rule_content" class="field-textarea" placeholder="写清楚满足条件和禁止动作" />
            </div>

            <div class="field-row">
              <label class="field-label" for="rule-priority">优先级</label>
              <select id="rule-priority" v-model="disciplineStore.ruleForm.priority" class="field-input">
                <option value="high">高</option>
                <option value="medium">中</option>
                <option value="low">低</option>
              </select>
            </div>

            <div class="field-row">
              <label class="field-label" for="rule-status">状态</label>
              <select id="rule-status" v-model="disciplineStore.ruleForm.status" class="field-input">
                <option value="active">启用</option>
                <option value="inactive">停用</option>
              </select>
            </div>

            <label class="checkbox-row field-row-full">
              <input v-model="disciplineStore.ruleForm.strong_reminder" type="checkbox" />
              <span>设为强提醒</span>
            </label>
          </div>

          <div class="button-row">
            <button class="primary-button" :disabled="disciplineStore.submittingRule" @click="submitRule">
              {{ disciplineStore.submittingRule ? '保存中...' : disciplineStore.isEditingRule ? '保存修改' : '保存纪律清单' }}
            </button>
            <button class="ghost-button" :disabled="disciplineStore.submittingRule" @click="disciplineStore.resetRuleForm">
              {{ disciplineStore.isEditingRule ? '取消编辑' : '重置' }}
            </button>
          </div>
        </div>

        <div class="card-block">
          <div class="result-header">
            <h4 class="panel-title">{{ disciplineStore.isEditingLesson ? '编辑血泪教训' : '血泪教训录入' }}</h4>
            <span v-if="disciplineStore.isEditingLesson" class="result-note">正在编辑现有案例，保存后会更新 CSV 记录。</span>
          </div>
          <div class="form-grid">
            <div class="field-row">
              <label class="field-label" for="lesson-time">时间 <span class="required-mark">*</span></label>
              <input id="lesson-time" v-model="disciplineStore.lessonForm.lesson_time" class="field-input" type="datetime-local" />
            </div>

            <div class="field-row">
              <label class="field-label" for="lesson-target-name">标的名称</label>
              <input id="lesson-target-name" v-model="disciplineStore.lessonForm.target_name" class="field-input" placeholder="例如：三六零" />
            </div>

            <div class="field-row">
              <label class="field-label" for="lesson-target-code">标的代码</label>
              <input id="lesson-target-code" v-model="disciplineStore.lessonForm.target_code" class="field-input" placeholder="例如：601360" />
            </div>

            <div class="field-row">
              <label class="field-label" for="lesson-concept">关联概念</label>
              <input id="lesson-concept" v-model="disciplineStore.lessonForm.concept_name" class="field-input" placeholder="例如：AI 应用" />
            </div>

            <div class="field-row field-row-full">
              <label class="field-label" for="mistake-action">错误行为 <span class="required-mark">*</span></label>
              <textarea id="mistake-action" v-model="disciplineStore.lessonForm.mistake_action" class="field-textarea" placeholder="描述具体错误动作" />
            </div>

            <div class="field-row field-row-full">
              <label class="field-label" for="original-thought">当时想法</label>
              <textarea id="original-thought" v-model="disciplineStore.lessonForm.original_thought" class="field-textarea" placeholder="当时的判断和理由" />
            </div>

            <div class="field-row field-row-full">
              <label class="field-label" for="actual-outcome">实际后果 <span class="required-mark">*</span></label>
              <textarea id="actual-outcome" v-model="disciplineStore.lessonForm.actual_outcome" class="field-textarea" placeholder="结果如何，亏损或错失什么" />
            </div>

            <div class="field-row field-row-full">
              <label class="field-label" for="trigger-reason">触发原因</label>
              <textarea id="trigger-reason" v-model="disciplineStore.lessonForm.trigger_reason" class="field-textarea" placeholder="什么情绪或情境导致犯错" />
            </div>

            <div class="field-row">
              <label class="field-label" for="linked-rule">对应纪律</label>
              <input id="linked-rule" v-model="disciplineStore.lessonForm.linked_rule" class="field-input" placeholder="关联一条纪律标题" />
            </div>

            <div class="field-row">
              <label class="field-label" for="improvement-action">改进动作</label>
              <input id="improvement-action" v-model="disciplineStore.lessonForm.improvement_action" class="field-input" placeholder="例如：开仓前二次核对" />
            </div>

            <div class="field-row">
              <label class="field-label" for="lesson-severity">严重等级</label>
              <select id="lesson-severity" v-model="disciplineStore.lessonForm.severity" class="field-input">
                <option value="high">高</option>
                <option value="medium">中</option>
                <option value="low">低</option>
              </select>
            </div>

            <label class="checkbox-row field-row-full">
              <input v-model="disciplineStore.lessonForm.show_on_dashboard" type="checkbox" />
              <span>显示到首页</span>
            </label>
          </div>

          <div class="button-row">
            <button class="primary-button" :disabled="disciplineStore.submittingLesson" @click="submitLesson">
              {{ disciplineStore.submittingLesson ? '保存中...' : disciplineStore.isEditingLesson ? '保存修改' : '保存血泪教训' }}
            </button>
            <button class="ghost-button" :disabled="disciplineStore.submittingLesson" @click="disciplineStore.resetLessonForm">
              {{ disciplineStore.isEditingLesson ? '取消编辑' : '重置' }}
            </button>
          </div>
        </div>
      </div>

      <p v-if="disciplineStore.error" class="error-text">{{ disciplineStore.error }}</p>
      <p v-else-if="disciplineStore.successMessage" class="success-text">{{ disciplineStore.successMessage }}</p>

      <div class="two-column discipline-grid">
        <div class="card-block">
          <div class="result-header">
            <h4 class="panel-title">纪律清单</h4>
            <span class="result-note">强提醒和高优先级规则会优先排前。</span>
          </div>
          <div v-if="disciplineStore.loadingRules" class="empty-hint">正在加载纪律清单...</div>
          <div v-else-if="disciplineStore.hasRules" class="list-stack">
            <article v-for="item in disciplineStore.rules" :key="item.id" class="rule-card">
              <div class="rule-header">
                <div>
                  <h5 class="rule-title">{{ item.rule_title }}</h5>
                  <p class="rule-meta">{{ item.rule_type }} / {{ priorityLabel(item.priority) }}</p>
                </div>
                <div class="tag-list">
                  <span v-if="item.strong_reminder === '1'" class="severity-chip severity-high">强提醒</span>
                  <span class="status-chip">{{ item.status === 'active' ? '启用' : '停用' }}</span>
                  <button class="ghost-button small-button" @click.stop="editRule(item)">编辑</button>
                  <button class="ghost-button small-button danger-button" @click.stop="deleteRule(item)">删除</button>
                </div>
              </div>
              <p class="rule-content">{{ item.rule_content }}</p>
            </article>
          </div>
          <div v-else class="empty-hint">暂无纪律清单。先录入一条规则。</div>
        </div>

        <div class="card-block">
          <div class="result-header">
            <h4 class="panel-title">血泪教训</h4>
            <span class="result-note">优先展示最近的高严重等级案例。</span>
          </div>
          <div v-if="disciplineStore.loadingLessons" class="empty-hint">正在加载血泪教训...</div>
          <div v-else-if="disciplineStore.hasLessons" class="list-stack">
            <article v-for="item in disciplineStore.lessons" :key="item.id" class="lesson-card">
              <div class="rule-header">
                <div>
                  <h5 class="rule-title">{{ item.mistake_action }}</h5>
                  <p class="rule-meta">{{ item.lesson_time }} / {{ item.target_name || item.concept_name || '未关联标的' }}</p>
                </div>
                <div class="tag-list">
                  <span class="severity-chip" :class="`severity-${item.severity}`">{{ priorityLabel(item.severity) }}</span>
                  <span v-if="item.show_on_dashboard === '1'" class="status-chip">首页展示</span>
                  <button class="ghost-button small-button" @click.stop="editLesson(item)">编辑</button>
                  <button class="ghost-button small-button danger-button" @click.stop="deleteLesson(item)">删除</button>
                </div>
              </div>
              <p class="rule-content">后果：{{ item.actual_outcome }}</p>
            </article>
          </div>
          <div v-else class="empty-hint">暂无血泪教训。先录入一条案例。</div>
        </div>
      </div>
    </PageSection>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

import PageSection from '@/components/common/PageSection.vue'
import { useDisciplineStore } from '@/stores/discipline'
import type { DisciplineLessonItem, DisciplineRuleItem } from '@/types/discipline'

const disciplineStore = useDisciplineStore()

onMounted(async () => {
  await disciplineStore.fetchRules()
  await disciplineStore.fetchLessons()
})

async function submitRule() {
  await disciplineStore.submitRule()
}

async function submitLesson() {
  await disciplineStore.submitLesson()
}

function editRule(item: DisciplineRuleItem) {
  disciplineStore.startEditRule(item)
}

function editLesson(item: DisciplineLessonItem) {
  disciplineStore.startEditLesson(item)
}

async function deleteRule(item: DisciplineRuleItem) {
  const confirmed = window.confirm(`确认删除纪律清单「${item.rule_title}」吗？`)
  if (!confirmed) {
    return
  }

  await disciplineStore.removeRule(item)
}

async function deleteLesson(item: DisciplineLessonItem) {
  const confirmed = window.confirm('确认删除这条血泪教训吗？')
  if (!confirmed) {
    return
  }

  await disciplineStore.removeLesson(item)
}

function priorityLabel(value: string) {
  if (value === 'high') return '高'
  if (value === 'low') return '低'
  return '中'
}
</script>

<style scoped>
.discipline-grid {
  align-items: start;
}

.panel-title {
  margin: 0 0 16px;
  font-size: 18px;
  color: var(--text);
}

.field-label,
.result-note,
.empty-hint,
.rule-meta {
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

.checkbox-row,
.button-row,
.result-header,
.rule-header,
.tag-list {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.checkbox-row {
  align-items: center;
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

.result-header,
.rule-header {
  justify-content: space-between;
  align-items: flex-start;
}

.list-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.rule-card,
.lesson-card {
  padding: 18px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: linear-gradient(180deg, #fff 0%, #f9fbff 100%);
}

.rule-title,
.rule-content {
  margin: 0;
  color: var(--text);
}

.rule-meta {
  margin: 4px 0 0;
}

.rule-content {
  margin-top: 12px;
}

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
  margin: 0;
  color: #c62828;
}

.success-text {
  margin: 0;
  color: #2e7d32;
}

@media (max-width: 900px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .result-header,
  .rule-header {
    flex-direction: column;
  }
}
</style>
