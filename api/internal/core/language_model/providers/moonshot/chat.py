#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/11/16 21:30
@Author   :314907015@qq.com
@File     :chat.py
"""
from typing import Any, Callable, Sequence

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_moonshot import ChatMoonshot

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(ChatMoonshot, BaseLanguageModel):
    """Moonshot（Kimi）聊天模型，使用OpenAI兼容协议，通过base_url指向Moonshot网关"""

    def get_num_tokens_from_messages(
        self,
        messages: Sequence[BaseMessage],
        tools: Sequence[dict[str, Any] | type | Callable] | None = None,
        **kwargs: Any,
    ) -> int:
        """langchain-openai的实现只支持OpenAI官方模型名，moonshot-v1系列会抛
        NotImplementedError，这里回退到langchain_core通用实现（tiktoken估算）。"""
        return BaseChatModel.get_num_tokens_from_messages(self, messages)
    ...
