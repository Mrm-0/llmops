#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/11/16 21:30
@Author   :314907015@qq.com
@File     :chat.py
"""
import os
from typing import Any

from langchain_openai import ChatOpenAI

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(ChatOpenAI, BaseLanguageModel):
    """智谱GLM聊天模型，使用OpenAI兼容协议，通过base_url指向智谱开放平台"""

    def __init__(self, **kwargs: Any) -> None:
        api_key = os.environ.get("ZHIPU_API_KEY")
        if api_key:
            kwargs.setdefault("api_key", api_key)
        super().__init__(**kwargs)
