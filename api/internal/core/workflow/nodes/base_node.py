#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/11/10 18:12
@Author   :314907015@qq.com
@File     :base_node.py
"""
from abc import ABC
from typing import Any, ClassVar

from langchain_core.runnables import RunnableSerializable

from internal.core.workflow.entities.node_entity import BaseNodeData


class BaseNode(RunnableSerializable, ABC):
    """工作流节点基类"""
    node_data: BaseNodeData