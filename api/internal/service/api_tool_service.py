#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/9/17 10:25
@Author   :314907015@qq.com
@File     :api_tool_service.py
"""
import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from injector import inject
from sqlalchemy import desc

from internal.core.tools.api_tools.entities import OpenAPISchema
from internal.exception import ValidateErrorException, NotFoundException
from internal.model import ApiToolProvider, ApiTool, Account
from internal.schema.api_tool_schema import (
    CreateApiToolReq,
    GetApiToolProvidersWithPageReq,
    UpdateApiToolProviderReq,
)
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from ..core.tools.api_tools.providers import ApiProviderManager


@inject
@dataclass
class ApiToolService(BaseService):
    """自定义API插件服务"""
    db: SQLAlchemy
    api_provider_manager: ApiProviderManager

    def create_api_tool_provider(self, req: CreateApiToolReq, account: Account) -> None:
        """创建自定义API工具"""
        # 1.检验并提取openapi_schema对应数据
        openapi_schema = self.parse_openapi_schema(req.openapi_schema.data)

        # 2.查询当前登录的账号是否已经创建了相同名称的工具提供者，如果是则抛出错误
        api_tool_provider = self.db.session.query(ApiToolProvider).filter_by(
            account_id=account.id,
            name=req.name.data
        ).one_or_none()
        if api_tool_provider:
            raise ValidateErrorException(f"该工具提供者名字{req.name.data}已存在")

        # 4.首先创建工具提供者，并获取工具提供者的id信息，然后再创建工具信息
        api_tool_provider = self.create(
            ApiToolProvider,
            account_id=account.id,
            name=req.name.data,
            icon=req.icon.data,
            description=openapi_schema.description,
            openapi_schema=req.openapi_schema.data,
            headers=req.headers.data
        )

        # 5.创建API工具并关联api_tool_provider
        for path, path_item in openapi_schema.paths.items():
            for method, method_item in path_item.items():
                self.create(
                    ApiTool,
                    account_id=account.id,
                    provider_id=api_tool_provider.id,
                    name=method_item.get("operationId"),
                    description=method_item.get("description"),
                    url=f"{openapi_schema.server}{path}",
                    method=method,
                    parameters=method_item.get("parameters", []),
                )

    def delete_api_tool_provider(self, provider_id: UUID, account: Account) -> None:
        """根据provider_id删除对应的提供者+工具的所有信息"""
        # 1.查找数据，检测provider_id数据存不存在，权限是否正确
        api_tool_provider = self.get(ApiToolProvider, provider_id)
        if api_tool_provider is None or api_tool_provider.account_id != account.id:
            raise NotFoundException("该工具提供者不存在")

        # 2.开启数据库的自动提交
        with self.db.auto_commit():
            # 3.删除提供者对应的工具信息
            self.db.session.query(ApiTool).filter(
                ApiTool.provider_id == provider_id,
                ApiTool.account_id == account.id
            ).delete()
            # 4.删除提供者信息
            self.db.session.delete(api_tool_provider)

    def update_api_tool_provider(self, provider_id: UUID, req: UpdateApiToolProviderReq, account: Account):
        """根据provider_id+req更新自定义API工具提供者信息"""
        # 1.根据provider_id获取自定义API信息并校验
        api_tool_provider = self.get(ApiToolProvider, provider_id)
        if api_tool_provider is None or api_tool_provider.account_id != account.id:
            raise ValidateErrorException("该工具提供者不存在")

        # 2.进行openapi_schema校验
        openapi_schema = self.parse_openapi_schema(req.openapi_schema.data)

        # 3.检查当前账号下是否已经创建了同名的工具提供者
        check_api_tool_provider = self.db.session.query(ApiToolProvider).filter(
            ApiToolProvider.id != provider_id,
            ApiToolProvider.account_id == account.id,
            ApiToolProvider.name == req.name.data
        ).one_or_none()
        if check_api_tool_provider:
            raise ValidateErrorException(f"工具提供者{req.name.data}已存在")

        # 4.开启数据库的自动提交
        with self.db.auto_commit():
            # 5.先删除工具提供者下的所有工具
            self.db.session.query(ApiTool).filter(
                ApiTool.provider_id == api_tool_provider.id,
                ApiTool.account_id == account.id,
            ).delete()

        # 6.修改工具提供者信息
        self.update(
            api_tool_provider,
            name=req.name.data,
            icon=req.icon.data,
            openapi_schema=req.openapi_schema.data,
            headers=req.headers.data,
        )

        # 7.新增工具信息以完成覆盖更新
        for path, path_item in openapi_schema.paths.items():
            for method, method_item in path_item.items():
                self.create(
                    ApiTool,
                    account_id=account.id,
                    provider_id=api_tool_provider.id,
                    name=method_item.get("operationId"),
                    description=method_item.get("description"),
                    url=f"{openapi_schema.server}{path}",
                    method=method,
                    parameters=method_item.get("parameters", []),
                )

    def get_api_tool_providers_with_page(self, req: GetApiToolProvidersWithPageReq, account: Account) -> tuple[
        list[Any], Paginator]:
        """获取自定义API工具服务提供者分页列表数据"""
        # 1.构建分页查询器
        paginator = Paginator(self.db, req)

        # 2.构建筛选器
        filters = [ApiToolProvider.account_id == account.id]
        if req.search_word.data:
            filters.append(ApiToolProvider.name.ilike(f"%{req.search_word.data}%"))

        # 3.执行分页并获取数据
        api_tool_providers = paginator.paginate(
            self.db.session.query(ApiToolProvider).filter(*filters).order_by(desc("created_at"))
        )

        return api_tool_providers, paginator

    def get_api_tool(self, provider_id: UUID, tool_name: str, account: Account) -> ApiTool:
        """根据provider_id+tool_name获取工具参数的详细信息"""
        api_tool = self.db.session.query(ApiTool).filter_by(
            provider_id=provider_id,
            name=tool_name
        ).one_or_none()
        if api_tool is None or api_tool.account_id != account.id:
            raise NotFoundException("该工具不存在")
        return api_tool

    def get_api_tool_provider(self, provider_id: UUID, account: Account) -> ApiToolProvider | None:
        """根据provider_id获取工具提供者的原始信息"""
        # 1.从数据库获取对应的数据
        api_tool_provider = self.get(ApiToolProvider, provider_id)

        # 验证数据是否为空，并且判断该数据是否属于登录的账号
        if api_tool_provider is None or api_tool_provider.account_id != account.id:
            raise NotFoundException("该工具提供者不存在")
        return api_tool_provider

    @classmethod
    def parse_openapi_schema(cls, openapi_schema_str: str) -> OpenAPISchema:
        """解析传递的openapi_schema字符串，如果出错则抛出错误"""
        try:
            data = json.loads(openapi_schema_str.strip())
            if not isinstance(data, dict):
                raise
        except Exception as e:
            raise ValidateErrorException(f"传递的数据必须符合OpenAPI规范的JSON字符串,错误是：{e}")

        return OpenAPISchema(**data)
