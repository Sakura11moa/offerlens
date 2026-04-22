<template>
  <el-card v-if="result">
    <template #header>
      <div class="header-row">
        <span>Analyze Result</span>
        <el-tag type="success">Score: {{ result.score }}</el-tag>
      </div>
    </template>

    <section>
      <h4>Strengths</h4>
      <el-tag v-for="item in result.strengths" :key="`s-${item}`" class="tag">{{ item }}</el-tag>
    </section>

    <section>
      <h4>Weaknesses</h4>
      <el-tag v-for="item in result.weaknesses" :key="`w-${item}`" type="warning" class="tag">{{ item }}</el-tag>
    </section>

    <section>
      <h4>Missing Keywords</h4>
      <el-tag v-for="item in result.missing_keywords" :key="`m-${item}`" type="info" class="tag">{{ item }}</el-tag>
    </section>

    <section>
      <h4>Rewrite Suggestions</h4>
      <ul>
        <li v-for="item in result.rewrite_suggestions" :key="`r-${item}`">{{ item }}</li>
      </ul>
    </section>

    <section>
      <h4>Interview Questions</h4>
      <ul>
        <li v-for="item in result.interview_questions" :key="`i-${item}`">{{ item }}</li>
      </ul>
    </section>

    <section>
      <h4>Summary</h4>
      <p>{{ result.summary }}</p>
    </section>
  </el-card>
</template>

<script setup lang="ts">
import type { AnalyzeResponse } from "../types/analyze";

defineProps<{
  result: AnalyzeResponse | null;
}>();
</script>

<style scoped>
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

section {
  margin-bottom: 16px;
}

h4 {
  margin: 0 0 8px;
}
</style>
