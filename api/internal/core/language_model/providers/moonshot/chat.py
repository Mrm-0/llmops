#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/11/16 21:30
@Author   :314907015@qq.com
@File     :chat.py
"""
from langchain_moonshot import ChatMoonshot

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(ChatMoonshot, BaseLanguageModel):
    """Moonshot（Kimi）聊天模型，使用OpenAI兼容协议，通过base_url指向Moonshot网关"""
    ...
