#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/11/15 15:22
@Author   :314907015@qq.com
@File     :chat.py
"""
from langchain_openai import ChatOpenAI

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(ChatOpenAI, BaseLanguageModel):
    """OpenAI聊天模型基类"""
    ...