<script lang="ts" setup>
import { useUpdateDraftAppConfig } from '@/hooks/use-app'
import { useOptimizePrompt } from '@/hooks/use-ai'
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'

// 1.定义自定义组件所需数据
const props = defineProps({
  app_id: { type: String, required: true },
  preset_prompt: { type: String, default: '', required: true }
})
const emits = defineEmits(['update:preset_prompt'])
const optimizeTriggerVisible = ref(false)
const origin_prompt = ref('')
const { handleUpdateDraftAppConfig } = useUpdateDraftAppConfig()
const { loading, optimize_prompt, handleOptimizePrompt } = useOptimizePrompt()

// 2.定义替换预设prompt处理器
const handleReplacePresetPrompt = () => {
  // 2.1 检测优化prompt是否为空
  if (optimize_prompt.value.trim() === '') {
    Message.warning('优化prompt为空，请重新生成')
    return
  }

  // 2.2 触发时间替换preset_prompt
  emits('update:preset_prompt', optimize_prompt.value)

  // 2.3 触发更新草稿配置函数
  handleUpdateDraftAppConfig(props.app_id, { preset_prompt: optimize_prompt.value })

  // 2.4 隐藏触发器
  optimizeTriggerVisible.value = false
}

// 3.提交优化prompt处理器
const handleSubmit = async () => {
  // 3.1 检测原始prompt是否为空
  if (origin_prompt.value.trim() === '') {
    Message.warning('原始prompt不能为空')
    return
  }

  // 3.2 发起请求获取数据
  await handleOptimizePrompt(origin_prompt.value)
}
</script>

<template>
  <div class="flex flex-col h-[calc(100vh-173px)]">
    <!-- 提示标题 -->
    <div class="flex items-center justify-between px-4 mb-4">
      <div class="text-gray-700 font-bold">人设与回复逻辑</div>
      <a-trigger
        v-model:popup-visible="optimizeTriggerVisible"
        :popup-translate="[0, 8]"
        :trigger="['click']"
        position="bl"
      >
        <a-button class="rounded-lg px-2" size="mini">
          <template #icon>
            <icon-sync />
          </template>
          优化
        </a-button>
        <template #content>
          <a-card class="rounded-lg w-[422px]">
            <div class="flex flex-col">
              <!-- 优化prompt -->
              <div v-if="optimize_prompt" class="mb-4 flex flex-col">
                <div
                  class="max-h-[321px] overflow-scroll scrollbar-w-none mb-2 text-gray-700 whitespace-pre-line"
                >
                  {{ optimize_prompt }}
                </div>
                <a-space v-if="!loading">
                  <a-button
                    class="rounded-lg"
                    size="small"
                    type="primary"
                    @click="handleReplacePresetPrompt"
                  >
                    替换
                  </a-button>
                  <a-button class="rounded-lg" size="small" @click="optimizeTriggerVisible = false">
                    退出
                  </a-button>
                </a-space>
              </div>
              <!-- 底部输入框 -->
              <div class="">
                <div
                  class="h-[50px] flex items-center gap-2 px-4 flex-1 border border-gray-200 rounded-full"
                >
                  <input
                    v-model="origin_prompt"
                    class="flex-1 outline-0"
                    placeholder="你希望如何编写或优化提示词"
                    type="text"
                  />
                  <a-button :loading="loading" shape="circle" type="text" @click="handleSubmit">
                    <template #icon>
                      <icon-send :size="16" class="!text-blue-700" />
                    </template>
                  </a-button>
                </div>
              </div>
            </div>
          </a-card>
        </template>
      </a-trigger>
    </div>
    <!-- 输入框容器 -->
    <div class="flex-1">
      <a-textarea
        :max-length="2000"
        :model-value="props.preset_prompt"
        class="h-full resize-none !bg-transparent !border-0 text-gray-700 px-1 preset-prompt-textarea"
        placeholder="请在这里输入Agent的人设与回复逻辑(预设prompt)"
        show-word-limit
        @blur="
          async () => {
            await handleUpdateDraftAppConfig(props.app_id, {
              preset_prompt: props.preset_prompt,
            })
          }
        "
        @update:model-value="(value) => emits('update:preset_prompt', value)"
      />
    </div>
  </div>
</template>

<style>
.preset-prompt-textarea {
  textarea {
    scrollbar-width: none;
  }
}
</style>
