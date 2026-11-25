<script setup lang="ts">
import LoginBanner from './components/LoginBanner.vue'
import LoginForm from './components/LoginForm.vue'
</script>

<template>
  <!-- 页面容器 -->
  <div class="flex h-screen bg-white">
    <!-- 顶部站点Logo -->
    <div class="fixed top-6 left-[22px] inline-flex items-center gap-2 z-50">
      <a-avatar :size="26" shape="square" class="bg-blue-700 rounded-md">
        <icon-apps :size="15" />
      </a-avatar>
      <span class="text-gray-900 font-bold text-sm">LLMOps AppBuilder</span>
    </div>
    <!-- 左侧banner -->
    <login-banner />
    <!-- 右侧表单 -->
    <div class="relative flex flex-1 items-center justify-center pb-10 bg-gradient-to-br from-white via-white to-blue-50/70">
      <!-- 登录表单 -->
      <login-form />
      <!-- 底部footer -->
      <div class="absolute right-0 bottom-0 w-full">
        <footer class="flex items-center justify-center h-10 text-gray-400 text-sm text-center">
          LLMOps AppBuilder · 让 AI 应用触手可及
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped></style>
