<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import MarkdownIt from 'markdown-it'
import DotFlashing from '@/components/DotFlashing.vue'
import { useAudioPlayer } from '@/hooks/use-audio'
import AgentThought from './AgentThought.vue'
// 固定使用浅色主题，避免系统深色模式把Markdown区域刷成黑色背景
import 'github-markdown-css/github-markdown-light.css'

const { textToAudioLoading, isPlaying, startAudioStream, stopAudioStream } = useAudioPlayer()


// 1.定义自定义组件所需数据
const props = defineProps({
  app: {
    type: Object,
    default: () => {
      return {}
    },
    required: true
  },
  enable_text_to_speech: { type: Boolean, default: false, required: false },
  message_id: { type: String, default: '', required: false },
  answer: { type: String, default: '', required: true },
  loading: { type: Boolean, default: false, required: false },
  latency: { type: Number, default: 0, required: false },
  total_token_count: { type: Number, default: 0, required: false },
  agent_thoughts: {
    type: Array as PropType<Record<string, any>[]>,
    default: () => [],
    required: true
  },
  suggested_questions: { type: Array as PropType<string[]>, default: () => [], required: false },
  message_class: { type: String, default: 'bg-slate-50', required: false }
})
const emits = defineEmits(['selectSuggestedQuestion'])
const md = MarkdownIt()
const compiledMarkdown = computed(() => {
  return md.render(props.answer)
})
</script>

<template>
  <div class="flex gap-2 group">
    <!-- 左侧图标 -->
    <a-avatar
      v-if="props.app?.icon"
      :image-url="props.app?.icon"
      :size="30"
      class="flex-shrink-0"
      shape="circle"
    />
    <a-avatar v-else :size="30" class="flex-shrink-0 bg-blue-700" shape="circle">
      <icon-apps />
    </a-avatar>
    <!-- 右侧名称与消息 -->
    <div class="flex-1 flex flex-col items-start gap-2">
      <!-- 应用名称 -->
      <div class="text-gray-700 font-bold">{{ props.app?.name }}</div>
      <!-- 推理步骤 -->
      <agent-thought :agent_thoughts="props.agent_thoughts" :loading="props.loading" />
      <!-- AI消息 -->
      <div
        v-if="props.loading && props.answer.trim() === ''"
        :class="`${props.message_class} border border-slate-200 shadow-sm text-gray-700 px-4 py-3 rounded-2xl break-all`"
      >
        <dot-flashing />
      </div>
      <div
        v-else
        :class="`${props.message_class} ai-markdown markdown-body border border-slate-200 shadow-sm text-gray-700 px-4 py-3 rounded-2xl break-all`"
        v-html="compiledMarkdown"
      ></div>
      <!-- 消息展示与操作 -->
      <div class="w-full flex items-center justify-between">
        <!-- 消息数据额外展示 -->
        <a-space class="text-xs">
          <template #split>
            <a-divider class="m-0" direction="vertical" />
          </template>
          <div class="flex items-center gap-1 text-gray-500">
            <icon-check />
            {{ props.latency.toFixed(2) }}s
          </div>
          <div class="text-gray-500">{{ props.total_token_count }} Tokens</div>
        </a-space>
        <!-- 播放音频&暂停播放 -->
        <div v-if="props.enable_text_to_speech" class="flex items-center gap-2">
          <template v-if="textToAudioLoading">
            <icon-loading class="hidden group-hover:block text-gray-500" />
          </template>
          <template v-else>
            <icon-pause
              v-if="isPlaying"
              class="hidden group-hover:block text-blue-700 cursor-pointer hover:text-blue-700"
              @click="() => stopAudioStream()"
            />
            <icon-play-circle
              v-else
              class="hidden group-hover:block text-gray-400 cursor-pointer hover:text-gray-700"
              @click="() => startAudioStream(props.message_id)"
            />
          </template>
        </div>
      </div>
      <!-- 建议问题列表 -->
      <div v-if="props.suggested_questions.length > 0" class="flex flex-col gap-2">
        <div
          v-for="(suggested_question, idx) in props.suggested_questions"
          :key="idx"
          class="px-4 py-1.5 border rounded-lg text-gray-700 cursor-pointer bg-white hover:bg-gray-50"
          @click="() => emits('selectSuggestedQuestion', suggested_question)"
        >
          {{ suggested_question }}
        </div>
      </div>
    </div>
  </div>
</template>

<style>
/* AI回答的Markdown区域：背景交由气泡控制，避免github-markdown-css自带的纯白/深色背景 */
.ai-markdown.markdown-body {
  background-color: transparent !important;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.75;
  color: #374151;
}

/* 首尾元素去除多余外边距，让内容与气泡内边距贴合 */
.ai-markdown.markdown-body > *:first-child {
  margin-top: 0 !important;
}
.ai-markdown.markdown-body > *:last-child {
  margin-bottom: 0 !important;
}
.ai-markdown.markdown-body p {
  margin-bottom: 10px;
}

/* 代码块、引用、表格等元素柔化，与浅色气泡协调 */
.ai-markdown.markdown-body pre {
  background-color: rgba(148, 163, 184, 0.12);
  border: 1px solid #e5e7eb;
  border-radius: 10px;
}
.ai-markdown.markdown-body code {
  background-color: rgba(148, 163, 184, 0.18);
  border-radius: 6px;
  padding: 0.15em 0.4em;
  color: #334155;
}
.ai-markdown.markdown-body pre code {
  background-color: transparent;
  padding: 0;
}
.ai-markdown.markdown-body blockquote {
  color: #4b5563;
  border-left: 0.25em solid #cbd5e1;
  background-color: rgba(148, 163, 184, 0.08);
  padding: 8px 14px;
  border-radius: 0 8px 8px 0;
}
.ai-markdown.markdown-body table tr {
  background-color: transparent;
}
.ai-markdown.markdown-body table tr:nth-child(2n) {
  background-color: rgba(148, 163, 184, 0.1);
}
.ai-markdown.markdown-body hr {
  background-color: #e5e7eb;
}
.ai-markdown.markdown-body a {
  color: #2563eb;
}
</style>
