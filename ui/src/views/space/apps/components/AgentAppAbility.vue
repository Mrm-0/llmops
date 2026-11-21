<script lang="ts" setup>
import LongTermMemoryAbilityItem from './abilities/LongTermMemoryAbilityItem.vue'
import OpeningAbilityItem from './abilities/OpeningAbilityItem.vue'
import SuggestedAfterAnswerAbilityItem from './abilities/SuggestedAfterAnswerAbilityItem.vue'
import ReviewConfigAbilityItem from './abilities/ReviewConfigAbilityItem.vue'
import DatasetsAbilityItem from './abilities/DatasetsAbilityItem.vue'
import ToolsAbilityItem from './abilities/ToolsAbilityItem.vue'
import WorkflowsAbilityItem from './abilities/WorkflowsAbilityItem.vue'
import SpeechToTextAbilityItem from './abilities/SpeechToTextAbilityItem.vue'
import TextToSpeechAbilitiItem from './abilities/TextToSpeechAbilitiItem.vue'

// 1.定义自定义组件所需数据
const props = defineProps({
  app_id: { type: String, default: '', required: true },
  draft_app_config: { type: Object, required: true }
})
const emits = defineEmits(['update:draft_app_config'])
const defaultActivateKeys = [
  'tools',
  'workflows',
  'datasets',
  'long_term_memory',
  'opening',
  'suggested_after_answer',
  'review_config',
  'speech_to_text',
  'text_to_speech'
]
</script>

<template>
  <div class="flex flex-col h-[calc(100vh-141px)]">
    <!-- 应用能力标题 -->
    <div class="p-4 text-gray-700 font-bold">应用能力</div>
    <!-- 应用能力列表 -->
    <div class="flex-1 overflow-scroll scrollbar-w-none">
      <a-collapse :bordered="false" :default-active-key="defaultActivateKeys">
        <template #expand-icon="{ active }">
          <icon-down v-if="active" />
          <icon-right v-else />
        </template>
        <!-- 扩展插件组件 -->
        <tools-ability-item
          :app_id="props.app_id"
          :tools="props.draft_app_config.tools"
          @update:tools="
            (tools) =>
              emits('update:draft_app_config', {
                ...props.draft_app_config,
                tools: tools,
              })
          "
        />
        <!-- 工作流组件 -->
        <workflows-ability-item
          :app_id="props.app_id"
          :workflows="props.draft_app_config.workflows"
          @update:workflows="
            (workflows) =>
              emits('update:draft_app_config', {
                ...props.draft_app_config,
                workflows,
              })
          "
        />
        <!-- 知识库组件 -->
        <datasets-ability-item
          :app_id="props.app_id"
          :datasets="props.draft_app_config.datasets"
          :retrieval_config="props.draft_app_config.retrieval_config"
          @update:retrieval_config="
            (retrieval_config) =>
              emits('update:draft_app_config', {
                ...props.draft_app_config,
                retrieval_config,
              })
          "
          @update:datasets="
            (datasets) =>
              emits('update:draft_app_config', {
                ...draft_app_config,
                datasets,
              })
          "
        />
        <!-- 长期记忆召回 -->
        <long-term-memory-ability-item
          :app_id="props.app_id"
          :long_term_memory="props.draft_app_config.long_term_memory"
          @update:long_term_memory="
            (long_term_memory) =>
              emits('update:draft_app_config', {
                ...props.draft_app_config,
                long_term_memory,
              })
          "
        />
        <!-- 对话开场白 -->
        <opening-ability-item
          :app_id="props.app_id"
          :opening_questions="props.draft_app_config.opening_questions"
          :opening_statement="props.draft_app_config.opening_statement"
          @update:opening_questions="
            (opening_questions) =>
              emits('update:draft_app_config', {
                ...props.draft_app_config,
                opening_questions,
              })
          "
          @update:opening_statement="
            (opening_statement) =>
              emits('update:draft_app_config', {
                ...props.draft_app_config,
                opening_statement,
              })
          "
        />
        <!-- 回答后生成建议问题 -->
        <suggested-after-answer-ability-item
          :app_id="props.app_id"
          :suggested_after_answer="props.draft_app_config.suggested_after_answer"
          @update:suggested_after_answer="
            (suggested_after_answer) =>
              emits('update:draft_app_config', {
                ...props.draft_app_config,
                suggested_after_answer,
              })
          "
        />
        <!-- 语音输入 -->
        <speech-to-text-ability-item
          :app_id="props.app_id"
          :speech_to_text="props.draft_app_config.speech_to_text"
          @update:speech_to_text="
            (speech_to_text) =>
              emits('update:draft_app_config', {
                ...props.draft_app_config,
                speech_to_text,
              })
          "
        />
        <!-- 语音输出 -->
        <text-to-speech-abiliti-item
          :app_id="props.app_id"
          :text_to_speech="props.draft_app_config.text_to_speech"
        />
        <!-- 内容审核 -->
        <review-config-ability-item
          :app_id="props.app_id"
          :review_config="props.draft_app_config.review_config"
        />
      </a-collapse>
    </div>
  </div>
</template>

<style>
.app-ability-item {
  .arco-collapse-item-header {
    background-color: transparent;
    border: none;
  }

  .arco-collapse-item-content {
    padding-left: 16px;
  }
}
</style>
