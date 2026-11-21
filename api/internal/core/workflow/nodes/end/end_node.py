#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/11/10 21:25
@Author   :314907015@qq.com
@File     :end_node.py
"""
import time
from typing import Any

from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state
from .end_entity import EndNodeData


class EndNode(BaseNode):
    """结束节点"""
    node_data : EndNodeData

    def invoke(
            self,
            state: WorkflowState,
            config: RunnableConfig | None = None,
            **kwargs: Any,
    ) -> WorkflowState:
        """结束节点执行函数，提出出状态中需要展示的数据，更新outputs"""
        # 1.提取节点中的数据
        start_at = time.perf_counter()
        outputs_dict = extract_variables_from_state(self.node_data.outputs, state)

        # 2.组装状态并返回
        return {
            "outputs": outputs_dict,
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCEEDED,
                    inputs={},
                    outputs=outputs_dict,
                    latency=(time.perf_counter() - start_at),
                )
            ]
        }
