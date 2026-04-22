<template>
  <div class="result-wrap">
    <el-card v-if="result" class="score-card">
      <div class="score-row">
        <div>
          <h2>匹配度总分</h2>
          <p>基于简历和岗位描述生成的当前匹配评估。</p>
        </div>
        <div class="score-block">
          <div class="score-value">{{ result.score }}</div>
          <div class="score-label">/ 100</div>
        </div>
      </div>
    </el-card>

    <div v-if="result" class="action-row">
      <el-button @click="copyResult">复制结果</el-button>
    </div>

    <div v-if="result" class="grid-cards">
      <el-card>
        <template #header>优势项</template>
        <div v-if="result.strengths.length" class="tag-list">
          <el-tag v-for="item in result.strengths" :key="`s-${item}`" class="tag">{{ item }}</el-tag>
        </div>
        <el-empty v-else description="暂无优势项" :image-size="72" />
      </el-card>

      <el-card>
        <template #header>风险项 / 薄弱项</template>
        <ul v-if="result.weaknesses.length" class="list">
          <li v-for="item in result.weaknesses" :key="`w-${item}`">{{ item }}</li>
        </ul>
        <el-empty v-else description="暂无薄弱项" :image-size="72" />
      </el-card>

      <el-card>
        <template #header>缺失关键词</template>
        <div v-if="result.missing_keywords.length" class="tag-list">
          <el-tag v-for="item in result.missing_keywords" :key="`m-${item}`" type="warning" class="tag">
            {{ item }}
          </el-tag>
        </div>
        <el-empty v-else description="暂无缺失关键词" :image-size="72" />
      </el-card>

      <el-card>
        <template #header>简历改写建议</template>
        <ul v-if="result.rewrite_suggestions.length" class="list">
          <li v-for="item in result.rewrite_suggestions" :key="`r-${item}`">{{ item }}</li>
        </ul>
        <el-empty v-else description="暂无改写建议" :image-size="72" />
      </el-card>

      <el-card>
        <template #header>面试题推荐</template>
        <ul v-if="result.interview_questions.length" class="list">
          <li v-for="item in result.interview_questions" :key="`i-${item}`">{{ item }}</li>
        </ul>
        <el-empty v-else description="暂无面试题推荐" :image-size="72" />
      </el-card>

      <el-card>
        <template #header>总结建议</template>
        <p v-if="result.summary" class="summary">{{ result.summary }}</p>
        <el-empty v-else description="暂无总结建议" :image-size="72" />
      </el-card>
    </div>

    <el-card v-else-if="loading" class="empty-card">
      <el-skeleton :rows="6" animated />
    </el-card>

    <el-card v-else class="empty-card">
      <el-empty description="粘贴简历和岗位描述后点击“开始分析”，结果会显示在这里。" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";

import type { AnalyzeResponse } from "../types/analyze";

const props = defineProps<{
  result: AnalyzeResponse | null;
  loading: boolean;
}>();

function buildCopyText(data: AnalyzeResponse): string {
  const lines = [
    "OfferLens 分析结果",
    "",
    `总结建议：${data.summary || "暂无"}`,
    "",
    "优势项：",
    ...(data.strengths.length ? data.strengths.map((item, index) => `${index + 1}. ${item}`) : ["暂无"]),
    "",
    "薄弱项：",
    ...(data.weaknesses.length ? data.weaknesses.map((item, index) => `${index + 1}. ${item}`) : ["暂无"]),
    "",
    "简历改写建议：",
    ...(data.rewrite_suggestions.length
      ? data.rewrite_suggestions.map((item, index) => `${index + 1}. ${item}`)
      : ["暂无"]),
    "",
    "面试题推荐：",
    ...(data.interview_questions.length
      ? data.interview_questions.map((item, index) => `${index + 1}. ${item}`)
      : ["暂无"]),
  ];

  return lines.join("\n");
}

async function copyResult() {
  if (!props.result) {
    return;
  }

  try {
    await navigator.clipboard.writeText(buildCopyText(props.result));
    ElMessage.success("分析结果已复制");
  } catch {
    ElMessage.error("复制失败，请检查剪贴板权限。");
  }
}
</script>

<style scoped>
.result-wrap {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.score-card {
  background: linear-gradient(135deg, #f7fbff, #eef5ff);
}

.score-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.score-row h2 {
  margin: 0 0 8px;
  word-break: break-word;
}

.score-row p {
  margin: 0;
  color: #606266;
  word-break: break-word;
}

.score-block {
  display: flex;
  align-items: baseline;
  color: #1f5eff;
}

.score-value {
  font-size: 48px;
  font-weight: 700;
  line-height: 1;
}

.score-label {
  font-size: 18px;
  margin-left: 4px;
}

.action-row {
  display: flex;
  justify-content: flex-end;
}

.grid-cards {
  display: grid;
  grid-template-columns: repeat(2, minmax(320px, 1fr));
  gap: 18px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  margin: 0;
  height: auto;
  white-space: normal;
  line-height: 1.5;
  padding-top: 6px;
  padding-bottom: 6px;
}

.list {
  margin: 0;
  padding-left: 20px;
  line-height: 1.7;
  word-break: break-word;
}

.summary {
  margin: 0;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.empty-card {
  min-height: 180px;
}

.grid-cards > * {
  min-width: 0;
}

.result-wrap :deep(.el-card) {
  border-radius: 16px;
}

.result-wrap :deep(.el-card__header) {
  font-weight: 600;
}

.result-wrap :deep(.el-card__body) {
  overflow: visible;
}

@media (max-width: 900px) {
  .grid-cards {
    grid-template-columns: 1fr;
  }

  .score-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .score-value {
    font-size: 42px;
  }
}

@media (max-width: 600px) {
  .action-row :deep(.el-button) {
    width: 100%;
  }

  .score-card :deep(.el-card__body) {
    padding: 18px;
  }

  .score-value {
    font-size: 36px;
  }

  .score-label {
    font-size: 16px;
  }

  .list {
    padding-left: 18px;
  }
}
</style>
