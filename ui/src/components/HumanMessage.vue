<script lang="ts" setup>
// 1.定义自定义组件所需数据
const props = defineProps({
  account: {
    type: Object,
    default: () => {
      return {}
    },
    required: true
  },
  query: { type: String, default: '', required: true },
  image_urls: { type: Array, default: () => [] }
})
</script>

<template>
  <div class="flex flex-row-reverse gap-2">
    <!-- 右侧头像 -->
    <a-avatar :image-url="props.account?.avatar" :size="30" class="flex-shrink-0" shape="circle" />
    <!-- 左侧昵称与消息（整体右对齐） -->
    <div class="flex flex-col items-end gap-2 max-w-[80%]">
      <!-- 账号昵称 -->
      <div class="text-gray-700 font-bold">{{ props.account?.name }}</div>
      <!-- 人类消息 -->
      <div
        class="bg-blue-100 border border-blue-200 text-gray-700 px-4 py-3 rounded-2xl break-all"
      >
        <a-image v-for="(image_url, idx) in props.image_urls" :key="idx" :src="String(image_url)" />
        {{ props.query }}
      </div>
    </div>
  </div>
</template>

<style scoped></style>
