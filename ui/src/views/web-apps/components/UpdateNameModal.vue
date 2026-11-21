<script lang="ts" setup>
import { useUpdateConversationName } from '@/hooks/use-conversation'
import type { Form, ValidatedError } from '@arco-design/web-vue'
import { ref, watch } from 'vue'

// 1.定义自定义组件所需数据
const props = defineProps({
  conversation_id: { type: String, default: '', required: false },
  visible: { type: Boolean, required: true },
  success_callback: { type: Function, required: false }
})
const emits = defineEmits(['update:visible', 'update:conversation_id'])
const {
  loading: updateConversationNameLoading,
  handleUpdateConversationName //
} = useUpdateConversationName()
const defaultForm = { name: '' }
const form = ref({ ...defaultForm })
const formRef = ref<InstanceType<typeof Form>>()

// 2.定义隐藏模态窗函数
const hideModal = () => emits('update:visible', false)

// 3.定义表单提交函数
const saveName = async ({ errors }: { errors: Record<string, ValidatedError> | undefined }) => {
  // 3.1 判断表单是否出错
  if (errors) return

  // 3.2 检测是保存还是新增，调用不同的API接口
  await handleUpdateConversationName(props.conversation_id, form.value.name)

  // 3.3 完成保存操作，隐藏模态窗并调用回调函数
  props.success_callback && props.success_callback(props.conversation_id, form.value.name)
  emits('update:visible', false)
}

// 4.监听模态窗显示状态变化
watch(
  () => props.visible,
  async (newValue) => {
    // 4.1 清除表单校验信息
    formRef.value?.resetFields()

    // 4.2 关闭弹窗，需要清空表单数据
    if (!newValue) {
      form.value = defaultForm
      emits('update:conversation_id', '')
    }
  }
)
</script>

<template>
  <a-modal
    :footer="false"
    :visible="props.visible"
    :width="520"
    hide-title
    modal-class="rounded-xl"
    @cancel="hideModal"
  >
    <!-- 顶部标题 -->
    <div class="flex items-center justify-between">
      <div class="text-lg font-bold text-gray-700">重命名</div>
      <a-button class="!text-gray-700" size="small" type="text" @click="hideModal">
        <template #icon>
          <icon-close />
        </template>
      </a-button>
    </div>
    <!-- 中间表单 -->
    <div class="pt-6">
      <a-form ref="formRef" :model="form" layout="vertical" @submit="saveName">
        <a-form-item
          :rules="[{ required: true, message: '会话名称不能为空' }]"
          asterisk-position="end"
          field="name"
          label="会话名称"
        >
          <a-input v-model:model-value="form.name" placeholder="请输入新会话名称" />
        </a-form-item>
        <!-- 底部按钮 -->
        <div class="flex items-center justify-between">
          <div class=""></div>
          <a-space :size="16">
            <a-button class="rounded-lg" @click="hideModal">取消</a-button>
            <a-button
              :loading="updateConversationNameLoading"
              class="rounded-lg"
              html-type="submit"
              type="primary"
            >
              确认
            </a-button>
          </a-space>
        </div>
      </a-form>
    </div>
  </a-modal>
</template>

<style scoped></style>
