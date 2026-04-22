<template>
  <el-card>
    <el-form label-position="top" @submit.prevent>
      <el-form-item label="Resume Content">
        <el-input
          v-model="localResumeText"
          type="textarea"
          :rows="10"
          placeholder="Paste your resume content"
          maxlength="20000"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="Job Description">
        <el-input
          v-model="localJobDescription"
          type="textarea"
          :rows="10"
          placeholder="Paste the job description"
          maxlength="20000"
          show-word-limit
        />
      </el-form-item>

      <el-button type="primary" :loading="loading" @click="submit">Start Analyze</el-button>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";

const props = defineProps<{
  resumeText: string;
  jobDescription: string;
  loading: boolean;
}>();

const emit = defineEmits<{
  (e: "update:resumeText", value: string): void;
  (e: "update:jobDescription", value: string): void;
  (e: "submit"): void;
}>();

const localResumeText = ref(props.resumeText);
const localJobDescription = ref(props.jobDescription);

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
