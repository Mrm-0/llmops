#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/11/16 20:40
@Author   :314907015@qq.com
@File     :chat.py
"""
from langchain_deepseek import ChatDeepSeek

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(ChatDeepSeek, BaseLanguageModel):
    """DeepSeek聊天模型"""
    ...
