<script lang="ts" setup>
import { ref, watch } from 'vue'
import { type Form, type ValidatedError } from '@arco-design/web-vue'
import { useCreateWorkflow, useGetWorkflow, useUpdateWorkflow } from '@/hooks/use-workflow'
import { useUploadImage } from '@/hooks/use-upload-file'

// 1.定义自定义组件所需数据
const props = defineProps({
  workflow_id: { type: String, default: '', required: false },
  visible: { type: Boolean, required: true },
  callback: { type: Function, required: false }
})
const emits = defineEmits(['update:visible', 'update:workflow_id'])
const { loading: createWorkflowLoading, handleCreateWorkflow } = useCreateWorkflow()
const { loading: updateWorkflowLoading, handleUpdateWorkflow } = useUpdateWorkflow()
const { workflow, loadWorkflow } = useGetWorkflow()
const { image_url, handleUploadImage } = useUploadImage()
const defaultForm = {
  fileList: [] as any,
  icon: '',
  name: '',
  tool_call_name: '',
  description: ''
}
const form = ref({ ...defaultForm })
const formRef = ref<InstanceType<typeof Form>>()

// 2.定义隐藏模态窗函数
const hideModal = () => emits('update:visible', false)

// 3.定义表单提交函数
const saveWorkflow = async ({ errors }: { errors: Record<string, ValidatedError> | undefined }) => {
  // 3.1 判断表单是否出错
  if (errors) return

  // 3.2 检测是保存还是新增，调用不同的API接口
  if (props.workflow_id) {
    await handleUpdateWorkflow(props.workflow_id, form.value)
  } else {
    await handleCreateWorkflow(form.value)
  }

  // 3.3 完成保存操作，隐藏模态窗并调用回调函数
  emits('update:visible', false)
  props.callback && props.callback()
}

// 4.监听模态窗显示状态变化
watch(
  () => props.visible,
  async (newValue) => {
    // 4.1 清除表单校验信息
    formRef.value?.resetFields()

    // 4.2 判断弹窗是打开还是关闭
    if (newValue) {
      // 4.3 开启弹窗，需要检测下是更新还是创建操作
      if (props.workflow_id) {
        // 4.4 调用接口获取工作流详情
        await loadWorkflow(props.workflow_id)

        // 4.5 更新表单数据
        form.value = {
          fileList: [{ uid: '1', name: '应用图标', url: String(workflow.value?.icon) }],
          icon: String(workflow.value?.icon),
          name: String(workflow.value?.name),
          tool_call_name: String(workflow.value?.tool_call_name),
          description: String(workflow.value?.description)
        }
      }
    } else {
      // 4.6 关闭弹窗，需要清空表单数据
      form.value = defaultForm
      formRef.value?.resetFields()
      emits('update:workflow_id', '')
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
      <div class="text-lg font-bold text-gray-700">
        {{ props.workflow_id === '' ? '创建工作流' : '编辑工作流' }}
      </div>
      <a-button class="!text-gray-700" size="small" type="text" @click="hideModal">
        <template #icon>
          <icon-close />
        </template>
      </a-button>
    </div>
    <!-- 中间表单 -->
    <div class="pt-6">
      <a-form ref="formRef" :model="form" layout="vertical" @submit="saveWorkflow">
        <a-form-item
          :rules="[{ required: true, message: '工作流图标不能为空' }]"
          field="fileList"
          hide-label
        >
          <a-upload
            v-model:file-list="form.fileList"
            :custom-request="
              (option) => {
                // 1.从option中提取数据
                const { fileItem, onSuccess, onError } = option

                // 2.使用普通异步函数完成上传
                const uploadTask = async () => {
                  try {
                    await handleUploadImage(fileItem.file as File)
                    form.icon = image_url
                    onSuccess(image_url)
                  } catch (error) {
                    onError(error)
                  }
                }
                uploadTask()

                return { abort: () => {} }
              }
            "
            :limit="1"
            :on-before-remove="
              async () => {
                form.icon = ''
                return true
              }
            "
            accept="image/png, image/jpeg"
            class="!w-auto mx-auto"
            image-preview
            list-type="picture-card"
          />
        </a-form-item>
        <a-form-item
          :rules="[{ required: true, message: '工作流名称不能为空' }]"
          asterisk-position="end"
          field="name"
          label="工作流名称"
        >
          <a-input
            v-model:model-value="form.name"
            :max-length="50"
            placeholder="请输入工作流名称"
            show-word-limit
          />
        </a-form-item>
        <a-form-item
          :rules="[{ required: true, message: '英文名称不能为空' }]"
          asterisk-position="end"
          field="tool_call_name"
          label="英文名称"
        >
          <a-input
            v-model:model-value="form.tool_call_name"
            :max-length="50"
            placeholder="英文名称将用于被大模型识别及调用"
            show-word-limit
          />
        </a-form-item>
        <a-form-item
          :rules="[{ required: true, message: '工作流描述不能为空' }]"
          asterisk-position="end"
          field="description"
          label="工作流描述"
        >
          <a-textarea
            v-model:model-value="form.description"
            :auto-size="{ minRows: 8, maxRows: 8 }"
            :max-length="1024"
            placeholder="请输入关于该工作流的描述信息，以便LLM能准确识别工作流的用途。"
            show-word-limit
          />
        </a-form-item>
        <!-- 底部按钮 -->
        <div class="flex items-center justify-between">
          <div class=""></div>
          <a-space :size="16">
            <a-button class="rounded-lg" @click="hideModal">取消</a-button>
            <a-button
              :loading="createWorkflowLoading || updateWorkflowLoading"
              class="rounded-lg"
              html-type="submit"
              type="primary"
            >
              保存
            </a-button>
          </a-space>
        </div>
      </a-form>
    </div>
  </a-modal>
</template>

<style scoped></style>
