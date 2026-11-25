#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/11/8 15:02
@Author   :314907015@qq.com
@File     :api_key.py
"""
from datetime import datetime

from sqlalchemy import (
    PrimaryKeyConstraint,
    Column,
    UUID,
    String,
    Boolean,
    DateTime,
    text,
    Index
)

from internal.extension.database_extension import db
from .account import Account


class ApiKey(db.Model):
    """API秘钥表模型"""
    __tablename__ = "api_key"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_api_key_id"),
        Index("api_key_account_id_idx", "account_id"),
        Index("api_key_api_key_idx", "api_key"),
    )

    id = Column(UUID, nullable=False, server_default=text("gen_random_uuid()"))
    account_id = Column(UUID, nullable=False)
    api_key = Column(String(255), nullable=False, server_default=text("''::character varying"))
    is_active = Column(Boolean, nullable=False, server_default=text("false"))
    remark = Column(String(255), nullable=False, server_default=text("''::character varying"))
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
    def account(self) -> "Account":
        """只读属性，返回该密钥归属的账号信息"""
        return db.session.get(Account, self.account_id)
