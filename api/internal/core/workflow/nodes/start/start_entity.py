#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/11/10 20:53
@Author   :314907015@qq.com
@File     :start_entity.py
"""
from pydantic import Field

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity


class StartNodeData(BaseNodeData):
    """开始节点数据"""
    inputs: list[VariableEntity] = Field(default_factory=list)  # 开始节点的输入变量信息
