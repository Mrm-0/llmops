#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/10/22 17:41
@Author   :314907015@qq.com
@File     :conversation.py
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    UUID,
    String,
    Text,
    DateTime,
    Boolean,
    PrimaryKeyConstraint,
    text, Integer, Numeric, Float, func, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from internal.extension.database_extension import db


class Conversation(db.Model):
    """交流会话模型"""
    __tablename__ = "conversation"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_conversation_id"),
        Index("conversation_app_id_idx", "app_id"),
        Index("conversation_app_created_by_idx", "created_by"),
    )

    id = Column(UUID, nullable=False, server_default=text("gen_random_uuid()"))
    app_id = Column(UUID, nullable=False)
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    summary = Column(Text, nullable=False, server_default=text("''::text"))
    is_pinned = Column(Boolean, nullable=False, server_default=text("false"))
    is_deleted = Column(Boolean, nullable=False, server_default=text("false"))
    invoke_from = Column(String(255), nullable=False, server_default=text("''::character varying"))
    created_by = Column(UUID, nullable=True)

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        default=datetime.now,
        onupdate=datetime.now,
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        default=datetime.now,
    )

    @property
    def is_new(self) -> bool:
        """只读属性，用于判断会话是否是第一次创建"""
        message_count = db.session.query(func.count(Message.id)).filter(
            Message.conversation_id == self.id
        ).scalar()

        return False if message_count > 1 else True


class Message(db.Model):
    """交流消息模型"""
    __tablename__ = "message"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_message_id"),
        Index("message_conversation_id_idx", "conversation_id"),
        Index("message_created_by_idx", "created_by"),
    )

    id = Column(UUID, nullable=False, server_default=text("gen_random_uuid()"))
    app_id = Column(UUID, nullable=False)
    conversation_id = Column(UUID, nullable=False)
    invoke_from = Column(String(255), nullable=False, server_default=text("''::character varying"))
    created_by = Column(UUID, nullable=False)

    # 消息关联的原始问题
    query = Column(Text, nullable=False, server_default=text("''::text"))
    image_urls = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    message = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    message_token_count = Column(Integer, nullable=False, server_default=text("0"))
    message_unit_price = Column(Numeric(10, 7), nullable=False, server_default=text("0.0"))
    message_price_unit = Column(Numeric(10, 4), nullable=False, server_default=text("0.0"))

    # 消息关联的答案信息
    answer = Column(Text, nullable=False, server_default=text("''::text"))
    answer_token_count = Column(Integer, nullable=False, server_default=text("0"))
    answer_unit_price = Column(Numeric(10, 7), nullable=False, server_default=text("0.0"))
    answer_price_unit = Column(Numeric(10, 4), nullable=False, server_default=text("0.0"))

    # 消息的相关统计信息
    latency = Column(Float, nullable=False, server_default=text("0.0"))
    is_deleted = Column(Boolean, nullable=False, server_default=text("false"))
    status = Column(String(255), nullable=False, server_default=text("''::character varying"))
    error = Column(Text, nullable=False, server_default=text("''::text"))
    total_token_count = Column(Integer, nullable=False, server_default=text("0"))
    total_price = Column(Numeric(10, 7), nullable=False, server_default=text("0.0"))

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        default=datetime.now,
        onupdate=datetime.now,
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        default=datetime.now,
    )

    # 智能体推理列表，创建表关联
    agent_thoughts = relationship(
        "MessageAgentThought",
        backref="msg",
        lazy="selectin",
        passive_deletes="all",
        uselist=True,
        foreign_keys=[id],
        primaryjoin="MessageAgentThought.message_id == Message.id",
    )

    @property
    def conversation(self) -> Conversation:
        """只读属性，返回该消息对应的会话记录"""
        return db.session.get(Conversation, self.conversation_id)


class MessageAgentThought(db.Model):
    """智能体消息推理模型，用于记录Agent生成最终消息答案时"""
    __tablename__ = "message_agent_thought"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_message_agent_thought_id"),
        Index("message_agent_thought_app_id_idx", "app_id"),
        Index("message_agent_thought_conversation_id_idx", "conversation_id"),
        Index("message_agent_thought_message_id_idx", "message_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("gen_random_uuid()"))
    app_id = Column(UUID, nullable=False)
    conversation_id = Column(UUID, nullable=False)
    message_id = Column(UUID, nullable=False)
    invoke_from = Column(String(255), nullable=False, server_default=text("''::character varying"))
    created_by = Column(UUID, nullable=False)

    position = Column(Integer, nullable=False, server_default=text("0"))

    event = Column(String(255), nullable=False, server_default=text("''::character varying"))
    thought = Column(Text, nullable=False, server_default=text("''::text"))
    observation = Column(Text, nullable=False, server_default=text("''::text"))

    tool = Column(String(255), nullable=False, server_default=text("''::character varying"))
    tool_input = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    message = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    message_token_count = Column(Integer, nullable=False, server_default=text("0"))
    message_unit_price = Column(Numeric(10, 7), nullable=False, server_default=text("0.0"))
    message_price_unit = Column(Numeric(10, 4), nullable=False, server_default=text("0.0"))

    answer = Column(Text, nullable=False, server_default=text("''::text"))
    answer_token_count = Column(Integer, nullable=False, server_default=text("0"))
    answer_unit_price = Column(Numeric(10, 7), nullable=False, server_default=text("0.0"))
    answer_price_unit = Column(Numeric(10, 4), nullable=False, server_default=text("0.0"))

    total_token_count = Column(Integer, nullable=False, server_default=text("0"))
    total_price = Column(Numeric(10, 7), nullable=False, server_default=text("0.0"))
    latency = Column(Float, nullable=False, server_default=text("0.0"))

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        default=datetime.now,
        onupdate=datetime.now,
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        default=datetime.now,
    )
