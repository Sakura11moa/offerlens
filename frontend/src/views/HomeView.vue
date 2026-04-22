<template>
  <div class="page">
    <el-card class="intro-card">
      <h1>OfferLens MVP</h1>
      <p>Paste your resume and job description to get AI-powered matching insights.</p>
    </el-card>

    <ResumeForm
      v-model:resumeText="resumeText"
      v-model:jobDescription="jobDescription"
      :loading="loading"
      @submit="handleAnalyze"
    />

    <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon class="mt" />

    <AnalyzeResult :result="result" class="mt" />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

import { analyzeResume } from "../api/analyze";
import AnalyzeResult from "../components/AnalyzeResult.vue";
import ResumeForm from "../components/ResumeForm.vue";
import type { AnalyzeResponse } from "../types/analyze";

const resumeText = ref("");
const jobDescription = ref("");
const loading = ref(false);
const errorMessage = ref("");
const result = ref<AnalyzeResponse | null>(null);

async function handleAnalyze() {
  errorMessage.value = "";
  result.value = null;

  if (!resumeText.value.trim() || !jobDescription.value.trim()) {
    errorMessage.value = "Resume and job description are required.";
    return;
  }

  loading.value = true;

  try {
    result.value = await analyzeResume({
      resume_text: resumeText.value,
      job_description: jobDescription.value,
    });
  } catch (error: unknown) {
    if (error instanceof Error) {
      errorMessage.value = error.message;
    } else {
      errorMessage.value = "Analyze failed";
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.page {
  max-width: 1000px;
  margin: 24px auto;
  padding: 0 16px 24px;
}

.intro-card {
  margin-bottom: 16px;
}

.mt {
  margin-top: 16px;
}

h1 {
  margin: 0 0 8px;
}

p {
  margin: 0;
  color: #606266;
}
</style>
