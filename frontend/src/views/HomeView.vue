<template>
  <div class="page">
    <el-card class="hero-card">
      <p class="eyebrow">OfferLens AI 求职助手</p>
      <h1>把简历和岗位描述贴进来，3 分钟看出你的面试通过率</h1>
      <p class="hero-subtitle">
        一次分析输出匹配分、优势项、风险项、缺失关键词、改写建议和面试题推荐，帮助你更快准备投递与面试。
      </p>
    </el-card>

    <section class="section-block">
      <div class="section-head">
        <div>
          <h2>输入区</h2>
          <p>粘贴简历和岗位描述后发起分析，可多次修改并重新生成。</p>
        </div>
      </div>

      <ResumeForm
        v-model:resumeText="resumeText"
        v-model:jobDescription="jobDescription"
        :loading="loading"
        :resume-error="resumeError"
        :job-description-error="jobDescriptionError"
        :min-length="MIN_TEXT_LENGTH"
        @submit="handleAnalyze"
        @fill-sample="handleFillSample"
        @clear="handleClear"
      />
    </section>

    <section ref="resultSectionRef" class="section-block result-section">
      <div class="section-head">
        <div>
          <h2>分析结果</h2>
          <p>结果会按模块展开，便于快速查看匹配分、风险点和改写建议。</p>
        </div>
      </div>

      <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon class="error-alert" />
      <AnalyzeResult :result="result" :loading="loading" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from "vue";

import { analyzeResume } from "../api/analyze";
import AnalyzeResult from "../components/AnalyzeResult.vue";
import ResumeForm from "../components/ResumeForm.vue";
import { SAMPLE_JOB_DESCRIPTION, SAMPLE_RESUME } from "../constants/sampleData";
import type { AnalyzeResponse } from "../types/analyze";

const MIN_TEXT_LENGTH = 30;

const resumeText = ref("");
const jobDescription = ref("");
const loading = ref(false);
const errorMessage = ref("");
const result = ref<AnalyzeResponse | null>(null);
const resumeError = ref("");
const jobDescriptionError = ref("");
const resultSectionRef = ref<HTMLElement | null>(null);

function validateText(text: string, label: string): string {
  const value = text.trim();

  if (!value) {
    return `请输入${label}。`;
  }

  if (value.length < MIN_TEXT_LENGTH) {
    return `${label}至少需要 ${MIN_TEXT_LENGTH} 个字符。`;
  }

  return "";
}

function clearErrors() {
  errorMessage.value = "";
  resumeError.value = "";
  jobDescriptionError.value = "";
}

watch(resumeText, () => {
  if (resumeError.value) {
    resumeError.value = validateText(resumeText.value, "简历内容");
  }
});

watch(jobDescription, () => {
  if (jobDescriptionError.value) {
    jobDescriptionError.value = validateText(jobDescription.value, "岗位描述");
  }
});

function handleFillSample() {
  resumeText.value = SAMPLE_RESUME;
  jobDescription.value = SAMPLE_JOB_DESCRIPTION;
  clearErrors();
}

function handleClear() {
  resumeText.value = "";
  jobDescription.value = "";
  result.value = null;
  clearErrors();
}

async function handleAnalyze() {
  clearErrors();

  resumeError.value = validateText(resumeText.value, "简历内容");
  jobDescriptionError.value = validateText(jobDescription.value, "岗位描述");

  if (resumeError.value || jobDescriptionError.value) {
    errorMessage.value = "请先补全输入内容后再开始分析。";
    return;
  }

  loading.value = true;

  try {
    result.value = await analyzeResume({
      resume_text: resumeText.value,
      job_description: jobDescription.value,
    });

    await nextTick();
    resultSectionRef.value?.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error: unknown) {
    if (error instanceof Error) {
      errorMessage.value = error.message;
    } else {
      errorMessage.value = "分析失败，请稍后重试。";
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 16px 40px;
}

.hero-card {
  margin-bottom: 20px;
}

.section-block {
  margin-top: 20px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 12px;
  margin-bottom: 12px;
}

.section-head h2 {
  margin: 0 0 6px;
  font-size: 22px;
  line-height: 1.2;
}

.section-head p {
  margin: 0;
  color: #606266;
  line-height: 1.6;
}

.eyebrow {
  margin: 0 0 10px;
  font-size: 13px;
  color: #4e5969;
  letter-spacing: 0.6px;
}

h1 {
  margin: 0;
  font-size: 32px;
  line-height: 1.3;
}

.hero-subtitle {
  margin: 12px 0 0;
  color: #606266;
  line-height: 1.7;
}

.result-section {
  min-width: 0;
}

.error-alert {
  margin-bottom: 12px;
}

@media (max-width: 1080px) {
  h1 {
    font-size: 28px;
  }

  .section-head {
    align-items: flex-start;
  }
}

@media (max-width: 600px) {
  .page {
    padding: 14px 12px 28px;
  }

  h1 {
    font-size: 24px;
    line-height: 1.4;
  }

  .section-block {
    margin-top: 16px;
  }

  .section-head {
    margin-bottom: 10px;
  }

  .section-head h2 {
    font-size: 20px;
  }
}
</style>
