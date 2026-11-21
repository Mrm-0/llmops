#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/11/11 10:24
@Author   :314907015@qq.com
@File     :llm_node.py
"""
import time
from typing import Any

from jinja2 import Template
from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from .llm_entity import LLMNodeData
from ...utils.helper import extract_variables_from_state


class LLMNode(BaseNode):
    """大语言模型节点"""
    node_data: LLMNodeData

    def invoke(
            self,
            state: WorkflowState,
            config: RunnableConfig | None = None,
            **kwargs: Any,
    ) -> WorkflowState:
        """大语言模型节点执行函数"""
        # 1.提取节点数据中的输入数据
        start_at = time.perf_counter()
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)

        # 2.使用jinja2格式模板信息
        template = Template(self.node_data.prompt)
        prompt_value = template.render(**inputs_dict)

        # 3.通过依赖管理器获取language_model_service并加载模型
        from app.http.module import injector
        from internal.service import LanguageModelService

        language_model_service = injector.get(LanguageModelService)
        llm = language_model_service.load_language_model(self.node_data.language_model_config)

        # 4.调用LLM并传递prompt后提取数据
        content = llm.invoke(prompt_value).content

        # 5.提取并构建输出数据结构
        outputs = {}
        if self.node_data.outputs:
            outputs[self.node_data.outputs[0].name] = content
        else:
            outputs['output'] = content

        # 6.构建响应状态并返回
        return {
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCEEDED,
                    inputs=inputs_dict,
                    outputs=outputs,
                    latency=(time.perf_counter() - start_at),
                )
            ]
        }
