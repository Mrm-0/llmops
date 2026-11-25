#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/10/22 21:42
@Author   :314907015@qq.com
@File     :token_buffer_memory.py
"""
from dataclasses import dataclass

from langchain_core.messages import AnyMessage, AIMessage, trim_messages, get_buffer_string
from sqlalchemy import desc

from internal.core.language_model.entities.model_entity import BaseLanguageModel
from internal.entity.conversation_entity import MessageStatus
from internal.model import Conversation, Message
from pkg.sqlalchemy import SQLAlchemy

# 每条消息的角色/分隔符固定开销，cl100k_base 下 OpenAI 的估算口径约为 3~4
_MESSAGE_OVERHEAD = 4

_encoding = None
_encoding_failed = False


def _get_encoding():
    """惰性加载 cl100k_base 编码器，失败则返回 None（退化为字符估算，不抛异常）"""
    global _encoding, _encoding_failed
    if _encoding is None and not _encoding_failed:
        try:
            import tiktoken

            _encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            # 例如离线环境首次加载需要下载 BPE 词表，失败时降级即可，不能影响对话主流程
            _encoding_failed = True
    return _encoding


def _estimate_by_chars(content: str) -> int:
    """无编码器时的兜底估算：ASCII 约 4 字符/token，CJK 约 1.5 字/token"""
    ascii_count = sum(1 for ch in content if ord(ch) < 128)
    other_count = len(content) - ascii_count
    return (ascii_count + 3) // 4 + (other_count * 3 + 4) // 5


def _count_tokens(messages: list[AnyMessage]) -> int:
    """估算消息列表的 token 数，不依赖具体模型名（用于 trim_messages 的 token_counter）"""
    encoding = _get_encoding()
    total = 0
    for message in messages:
        content = message.content
        if not isinstance(content, str):
            content = str(content)
        total += (len(encoding.encode(content)) if encoding else _estimate_by_chars(content))
        total += _MESSAGE_OVERHEAD
    return total


@dataclass
class TokenBufferMemory:
    """基于token计数的缓冲记忆组件"""
    db: SQLAlchemy
    conversation: Conversation
    model_instance: BaseLanguageModel

    def get_history_prompt_messages(
            self,
            max_token_limit: int = 2000,
            message_limit: int = 10
    ) -> list[AnyMessage]:
        """根据传递的token限制和消息条数限制获取指定会话模型的历史消息列表"""
        # 1.判断会话模型是否存在，不存在则返回空列表
        if self.conversation is None:
            return []

        # 2.查询该会话的消息列表，并且使用时间进行倒序排序
        messages = self.db.session.query(Message).filter(
            Message.conversation_id == self.conversation.id,
            Message.answer != '',
            Message.is_deleted == False,
            Message.status.in_([MessageStatus.NORMAL, MessageStatus.STOP, MessageStatus.TIMEOUT])
        ).order_by(desc('created_at')).limit(message_limit).all()
        messages = list(reversed(messages))

        # 3.将message转换成LangChain消息列表
        prompt_messages = []
        for message in messages:
            prompt_messages.extend([
                self.model_instance.convert_to_human_message(message.query, message.image_urls),
                AIMessage(content=message.answer)
            ])

        # 4.调用LangChain继承的trim_messages函数剪切消息列表
        return trim_messages(
            messages=prompt_messages,
            max_tokens=max_token_limit,
            token_counter=_count_tokens,
            strategy="last"
        )

    def get_history_prompt_text(
            self,
            human_prefix: str = "Human",
            ai_prefix: str = "AI",
            max_token_limit: int = 2000,
            message_limit: int = 10
    ) -> str:
        """根据传递的数据获取指定会话历史消息提示文本(短期记忆的文本模型，用于文本生成模型)"""
        # 1.根据传递的信息获取指定会话
        messages = self.get_history_prompt_messages(max_token_limit, message_limit)

        # 2.调用LangChain集成的get_buffer_string()函数将消息列表转换成文本
        return get_buffer_string(messages, human_prefix, ai_prefix)
