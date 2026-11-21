#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/11/8 16:01
@Author   :314907015@qq.com
@File     :api_key_service.py
"""
import secrets
from dataclasses import dataclass
from uuid import UUID

from injector import inject
from sqlalchemy import desc

from internal.exception import NotFoundException, ForbiddenException
from internal.model import Account, ApiKey
from internal.schema.api_key_schema import CreateApiKeyReq
from pkg.paginator import PaginatorReq, Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class ApiKeyService(BaseService):
    """api秘钥服务"""
    db: SQLAlchemy

    def create_api_key(self, req: CreateApiKeyReq, account: Account) -> ApiKey:
        """根据传递的信息创建api秘钥"""
        return self.create(
            ApiKey,
            account_id=account.id,
            api_key=self.generate_api_key(),
            is_active=req.is_active.data,
            remark=req.remark.data,
        )

    def get_api_key(self, api_key_id: UUID, account: Account) -> ApiKey:
        """根据传递的id获取api_key"""
        api_key = self.get(ApiKey, api_key_id)
        if not api_key:
            raise NotFoundException("该api_key不存在")
        if api_key.account_id != account.id:
            raise ForbiddenException("该用户无权限查找此api_key")
        return api_key

    def update_api_key(self, api_key_id: UUID, account: Account, **kwargs) -> ApiKey:
        """根据传递的信息更新api_key"""
        api_key = self.get_api_key(api_key_id, account)
        self.update(api_key, **kwargs)
        return api_key

    def delete_api_key(self, api_key_id: UUID, account: Account) -> ApiKey:
        """根据传递的id删除api_key"""
        api_key = self.get_api_key(api_key_id, account)
        self.delete(api_key)
        return api_key

    def get_api_key_by_credential(self, api_key: str) -> ApiKey:
        """根据传递的凭证信息获取ApiKey信息"""
        return self.db.session.query(ApiKey).filter(
            ApiKey.api_key == api_key
        ).one_or_none()

    def get_api_keys_with_page(self, req: PaginatorReq, account: Account) -> tuple[list[ApiKey], Paginator]:
        """根据传递的信息获取api_key分页列表数据"""
        paginator = Paginator(db=self.db, req=req)

        api_keys = paginator.paginate(
            self.db.session.query(ApiKey).filter(
                ApiKey.account_id == account.id
            ).order_by(desc("created_at"))
        )

        return api_keys, paginator

    @classmethod
    def generate_api_key(cls, api_key_prefix: str = "llmops-v1/") -> str:
        """生成一个长度为48的api秘钥，携带前缀"""
        return api_key_prefix + secrets.token_urlsafe(48)
