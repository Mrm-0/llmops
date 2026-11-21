#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/8/24 13:48
@Author   :314907015@qq.com
@File     :app.py
"""
from sqlalchemy import (
    Column,
    UUID,
    String,
    Text,
    DateTime,
    PrimaryKeyConstraint,
    text,
    Integer, Index,
)
from sqlalchemy.dialects.postgresql import JSONB

from internal.entity.app_entity import DEFAULT_APP_CONFIG, AppConfigType, AppStatus
from internal.entity.conversation_entity import InvokeFrom
from internal.extension.database_extension import db
from internal.lib.helper import generate_random_string
from .conversation import Conversation


class App(db.Model):
    """AI应用基础"""
    __tablename__ = "app"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_id"),
        Index("app_account_id_idx", "account_id"),
        Index("app_token_idx", "token"),
    )

    id = Column(UUID, nullable=False, server_default=text("gen_random_uuid()"))
    account_id = Column(UUID, nullable=False)
    app_config_id = Column(UUID, nullable=True)
    draft_app_config_id = Column(UUID, nullable=True)
    debug_conversation_id = Column(UUID, nullable=True)
    name = Column(String(255), nullable=False, server_default=text("''::character varying"))
    icon = Column(String(255), nullable=False, server_default=text("''::character varying"))
    description = Column(Text, nullable=False, server_default=text("''::text"))
    token = Column(String(255), nullable=True, server_default=text("''::character varying"))
    status = Column(String(255), nullable=False, server_default=text("''::character varying"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
    )

    @property
    def app_config(self) -> "AppConfig":
        """只读属性，返回当前的运行配置"""
        if not self.app_config_id:
            return None
        return db.session.get(AppConfig, self.app_config_id)

    @property
    def draft_app_config(self) -> "AppConfigVersion":
        """只读属性，返回当前应用的草稿配置"""
        # 1.获取当前应用的草稿配置
        app_config_version = db.session.query(AppConfigVersion).filter(
            AppConfigVersion.app_id == self.id,
            AppConfigVersion.config_type == AppConfigType.DRAFT,
        ).one_or_none()

        # 2.检测配置是否存在，如果不存在则创建一个默认值
        if not app_config_version:
            app_config_version = AppConfigVersion(
                app_id=self.id,
                version=0,
                config_type=AppConfigType.DRAFT,
                **DEFAULT_APP_CONFIG,
            )
            db.session.add(app_config_version)
            db.session.commit()

        return app_config_version

    @property
    def debug_conversation(self) -> "Conversation":
        """获取应用的调试会话记录"""
        # 1.根据debug_conversion_id获取调试会话记录
        debug_conversion = None
        if self.debug_conversation_id is not None:
            debug_conversion = db.session.query(Conversation).filter(
                Conversation.id == self.debug_conversation_id,
                Conversation.invoke_from == InvokeFrom.DEBUGGER,
            ).one_or_none()

        # 2.检测数据是否存在，不存在则创建
        if not self.debug_conversation_id or debug_conversion is None:
            # 3.开启数据库自动提交上下文
            with db.auto_commit():
                # 4.创建应用调试会话记录并刷新获取会话id
                debug_conversion = Conversation(
                    app_id=self.id,
                    name="New Conversation",
                    invoke_from=InvokeFrom.DEBUGGER,
                    created_by=self.account_id
                )
                db.session.add(debug_conversion)
                db.session.flush()

                # 5.更新当前记录的debug_conversation_id
                self.debug_conversation_id = debug_conversion.id

        return debug_conversion

    @property
    def token_with_default(self) -> str:
        """获取带有默认值的token"""
        # 1.判断状态是否为已发布
        if self.status != AppStatus.PUBLISHED:
            # 2.非发布的情况下需要清空数据，并提交更新
            if self.token is not None or self.token != "":
                self.token = None
                db.session.commit()
            return ""

        # 3.已发布状态需判断token是否存在，不存在则生成
        if self.token is None or self.token == "":
            self.token = generate_random_string(16)
            db.session.commit()

        return self.token


class AppConfig(db.Model):
    """应用配置模型"""
    __tablename__ = "app_config"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_config_id"),
        Index("app_config_app_id_idx", "app_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("gen_random_uuid()"))
    app_id = Column(UUID, nullable=False)
    model_config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    dialog_round = Column(Integer, nullable=False, server_default=text("0"))
    preset_prompt = Column(Text, nullable=False, server_default=text("''::text"))
    tools = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    workflows = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    retrieval_config = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    long_term_memory = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    opening_statement = Column(Text, nullable=False, server_default=text("''::text"))
    opening_questions = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    speech_to_text = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    text_to_speech = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    review_config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
    )

    @property
    def app_dataset_joins(self) -> list["AppDatasetJoin"]:
        """只读属性，获取配置的关联知识库"""
        return (
            db.session.query(AppDatasetJoin).filter(
                AppDatasetJoin.app_id == self.id,
            ).all()
        )


class AppConfigVersion(db.Model):
    """应用配置版本历史表，用于储存草稿配置+历史发布配置"""
    __tablename__ = "app_config_version"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_config_version_id"),
        Index("app_config_version_app_id_idx", "app_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("gen_random_uuid()"))
    app_id = Column(UUID, nullable=False)
    model_config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    dialog_round = Column(Integer, nullable=False, server_default=text("0"))
    preset_prompt = Column(Text, nullable=False, server_default=text("''::text"))
    tools = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    workflows = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    datasets = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    retrieval_config = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    long_term_memory = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    opening_statement = Column(Text, nullable=False, server_default=text("''::text"))
    opening_questions = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    speech_to_text = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    text_to_speech = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    review_config = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    version = Column(Integer, nullable=False, server_default=text("0"))
    config_type = Column(String(255), nullable=False, server_default=text("''::character varying"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
    )


class AppDatasetJoin(db.Model):
    """应用知识库关联表模型"""
    __tablename__ = "app_dataset_join"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_dataset_join_id"),
        Index("app_dataset_join_app_id_dataset_id_idx", "app_id", "dataset_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("gen_random_uuid()"))
    app_id = Column(UUID, nullable=False)
    dataset_id = Column(UUID, nullable=False)
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)")
    )
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)"))
