#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/11/8 15:14
@Author   :314907015@qq.com
@File     :end_user.py
"""
from datetime import datetime

from sqlalchemy import (
    PrimaryKeyConstraint,
    Column,
    UUID,
    DateTime,
    text, Index
)

from internal.extension.database_extension import db


class EndUser(db.Model):
    """终端用户表模型"""
    __tablename__ = "end_user"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_end_user_id"),
        Index("end_user_tenant_id_idx", "tenant_id"),
        Index("end_user_app_id_idx", "app_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID, nullable=False)
    app_id = Column(UUID, nullable=False)
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
