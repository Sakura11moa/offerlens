<template>
  <div class="app-shell">
    <HomeView />
  </div>
</template>

<script setup lang="ts">
import HomeView from "./views/HomeView.vue";
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  background:
    radial-gradient(circle at top, rgba(31, 94, 255, 0.08), transparent 28%),
    linear-gradient(180deg, #f6f8fc 0%, #eef3f8 100%);
}
</style>
