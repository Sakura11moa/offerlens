<template>
  <el-card class="form-card">
    <template #header>
      <div class="card-header">
        <div>
          <h2>输入简历与岗位描述</h2>
          <p>每个输入框至少填写 {{ minLength }} 个字符，系统才会给出更有价值的分析结果。</p>
        </div>
        <div class="header-actions">
          <el-button :disabled="loading" @click="emit('fillSample')">填入示例</el-button>
          <el-button :disabled="loading" @click="emit('clear')">清空输入</el-button>
        </div>
      </div>
    </template>

    <el-form label-position="top" @submit.prevent>
      <el-form-item label="简历内容" :error="resumeError">
        <el-input
          v-model="localResumeText"
          type="textarea"
          :rows="10"
          placeholder="请输入工作经历、项目经历、技术栈和可量化成果，例如性能提升、成本下降、效率提升等"
          maxlength="20000"
          show-word-limit
          :disabled="loading"
        />
        <div class="field-meta">当前 {{ resumeLength }} 字，建议不少于 {{ minLength }} 字</div>
      </el-form-item>

      <el-form-item label="岗位描述（JD）" :error="jobDescriptionError">
        <el-input
          v-model="localJobDescription"
          type="textarea"
          :rows="10"
          placeholder="请输入岗位职责、必备技能、加分项、业务背景和面试关注点"
          maxlength="20000"
          show-word-limit
          :disabled="loading"
        />
        <div class="field-meta">当前 {{ jobDescriptionLength }} 字，建议不少于 {{ minLength }} 字</div>
      </el-form-item>

      <div class="form-footer">
        <el-button type="primary" :loading="loading" :disabled="loading || !canSubmit" @click="submit">
          {{ loading ? "正在分析简历与岗位匹配度..." : "开始分析" }}
        </el-button>
      </div>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

const props = defineProps<{
  resumeText: string;
  jobDescription: string;
  loading: boolean;
  resumeError: string;
  jobDescriptionError: string;
  minLength: number;
}>();

const emit = defineEmits<{
  (e: "update:resumeText", value: string): void;
  (e: "update:jobDescription", value: string): void;
  (e: "submit"): void;
  (e: "fillSample"): void;
  (e: "clear"): void;
}>();

const localResumeText = ref(props.resumeText);
const localJobDescription = ref(props.jobDescription);

const resumeLength = computed(() => localResumeText.value.trim().length);
const jobDescriptionLength = computed(() => localJobDescription.value.trim().length);

const canSubmit = computed(() => {
  return resumeLength.value >= props.minLength && jobDescriptionLength.value >= props.minLength;
});

watch(
  () => props.resumeText,
  (value) => {
    localResumeText.value = value;
  },
);

watch(
  () => props.jobDescription,
  (value) => {
    localJobDescription.value = value;
  },
);

watch(localResumeText, (value) => emit("update:resumeText", value));
watch(localJobDescription, (value) => emit("update:jobDescription", value));

function submit() {
  emit("submit");
}
</script>

<style scoped>
.form-card {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.card-header h2 {
  margin: 0 0 6px;
  font-size: 20px;
}

.card-header p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.field-meta {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
}

.form-footer {
  margin-top: 8px;
}

.form-card :deep(.el-textarea__inner) {
  line-height: 1.7;
  padding: 14px 16px;
}

@media (max-width: 900px) {
  .card-header {
    flex-direction: column;
  }
}

@media (max-width: 600px) {
  .header-actions {
    width: 100%;
  }

  .header-actions :deep(.el-button) {
    flex: 1 1 0;
    min-width: 0;
  }

  .form-footer :deep(.el-button) {
    width: 100%;
  }
}
</style>
