#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/11/16 20:40
@Author   :314907015@qq.com
@File     :chat.py
"""
from typing import Any, Callable, Sequence

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_deepseek import ChatDeepSeek

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(ChatDeepSeek, BaseLanguageModel):
    """DeepSeek聊天模型"""

    def get_num_tokens_from_messages(
        self,
        messages: Sequence[BaseMessage],
        tools: Sequence[dict[str, Any] | type | Callable] | None = None,
        **kwargs: Any,
    ) -> int:
        """计算消息列表的token数。

        langchain-openai 的实现（ChatDeepSeek继承而来）只支持OpenAI官方模型名
        （gpt-3.5/gpt-4系列），遇到deepseek系列会直接抛出
        NotImplementedError: get_num_tokens_from_messages() is not presently implemented。
        这里回退到langchain_core的通用实现：逐条消息累加get_num_tokens，
        底层通过tiktoken cl100k_base编码估算，对DeepSeek模型足够精确。
        """
        return BaseChatModel.get_num_tokens_from_messages(self, messages)
    ...
