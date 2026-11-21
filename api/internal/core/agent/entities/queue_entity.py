#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/10/23 17:53
@Author   :314907015@qq.com
@File     :queue_entity.py
"""
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from internal.entity.conversation_entity import MessageStatus


class QueueEvent(str, Enum):
    """队列事件枚举类型"""
    LONG_TERM_MEMORY_RECALL = "long_term_memory_recall"  # 长期记忆召回事件
    AGENT_THOUGHT = "agent_thought"  # 智能体观察事件
    AGENT_MESSAGE = "agent_message"  # 智能体消息事件
    AGENT_ACTION = "agent_action"  # 智能体动作
    DATASET_RETRIEVAL = "dataset_retrieval"  # 知识库检索事件
    AGENT_END = "agent_end"  # 智能体结束事件
    STOP = "stop"  # 智能体停止事件
    ERROR = "error"  # 智能体错误事件
    TIMEOUT = "timeout"  # 智能体超时事件
    PING = "ping"  # ping联通事件


class AgentThought(BaseModel):
    """智能体推理观察输出内容"""
    id: UUID
    task_id: UUID

    # 事件的推理与观察
    event: QueueEvent
    thought: str = ""
    observation: str = ""

    # 工具相关的字段
    tool: str = ""
    tool_input: dict = Field(default_factory=dict)

    # 消息相关的数据
    message: list[dict] = Field(default_factory=list)
    message_token_count: int = 0
    message_unit_price: float = 0
    message_price_unit: float = 0

    # 答案相关的数据
    answer: str = ""
    answer_token_count: int = 0
    answer_unit_price: float = 0
    answer_price_unit: float = 0

    # Agent推理统计相关
    total_token_count: int = 0
    total_price: float = 0
    latency: float = 0


class AgentResult(BaseModel):
    """智能体推理观察最终结果"""
    query: str = ""

    message: list[dict] = Field(default_factory=list)
    message_token_count: int = 0
    message_unit_price: float = 0
    message_price_unit: float = 0

    answer: str = ""
    answer_token_count: int = 0
    answer_unit_price: float = 0
    answer_price_unit: float = 0

    total_token_count: int = 0
    total_price: float = 0
    latency: float = 0

    status: str = MessageStatus.NORMAL
    error: str = ""

    agent_thoughts: list[AgentThought] = Field(default_factory=list)
