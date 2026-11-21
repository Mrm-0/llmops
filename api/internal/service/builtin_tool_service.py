#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/9/14 09:04
@Author   :314907015@qq.com
@File     :builtin_tool_service.py
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from injector import inject
from pydantic import BaseModel
import mimetypes
from flask import current_app

from internal.core.tools.builtin_tools.categories import BuiltinCategoryManager
from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.exception import NotFoundException


@inject
@dataclass
class BuiltinToolService:
    """内置工具服务"""
    builtin_tool_manager: BuiltinProviderManager
    builtin_category_manager: BuiltinCategoryManager

    def get_builtin_tools(self):
        """获取LLMOps中所有的内置提供商+对应工具的信息"""
        # 1.获取所有内置提供商
        providers = self.builtin_tool_manager.get_providers()

        # 2.遍历提供商并提取所有工具信息
        builtin_tools = []
        for provider in providers:
            provider_entity = provider.provider_entity
            builtin_tool = {
                **provider_entity.model_dump(exclude={"icon"}),
                "tools": []
            }
            # 3.遍历循环所有提供商的工具实体

            for tool_entity in provider.get_tool_entities():
                # 4.构建工具实体信息,从提供商中获取工具函数
                tool = provider.get_tool(tool_entity.name)
                tool_dict = {
                    **tool_entity.model_dump(),
                    "inputs": self.get_tool_inputs(tool)  # 根据工具函数获取传入参数信息
                }

                builtin_tool["tools"].append(tool_dict)

            builtin_tools.append(builtin_tool)

        return builtin_tools

    def get_provider_tool(self, provider_name: str, tool_name: str) -> dict:
        """根据提供商+工具名字，获取指定的工具信息"""
        # 1.获取内置提供商
        provider = self.builtin_tool_manager.get_provider(provider_name)
        if provider is None:
            raise NotFoundException(f"该提供商{provider_name}不存在")

        # 2.根据工具名字获取提供商的指定工具
        tool_entity = provider.get_tool_entity(tool_name)
        if tool_entity is None:
            raise NotFoundException(f"该工具{tool_name}不存在")

        # 3.组装提供商和工具实体信息
        provider_entity = provider.provider_entity
        tool = provider.get_tool(tool_name)
        builtin_tool = {
            "provider": {**provider_entity.model_dump(exclude={"icon", "create_at"}), },
            **tool_entity.model_dump(),
            "create_at": provider_entity.create_at,
            "inputs": self.get_tool_inputs(tool)
        }

        return builtin_tool

    def get_provider_icon(self, provider_name: str) -> tuple[bytes, str]:
        """根据提供商名称获取icon图标流信息"""
        # 1.获取对应的工具提供商
        provider = self.builtin_tool_manager.get_provider(provider_name)
        if provider is None:
            raise NotFoundException(f"该提供商{provider_name}不存在")

        # 2.获取项目的根路径信息
        root_path = Path(current_app.root_path).parents[1]

        # 3.拼接得到的提供商所在的文件夹
        provider_path = root_path / "internal" / "core" / "tools" / "builtin_tools" / "providers" / provider_name

        # 4.拼接得到icon路径
        icon_path = provider_path / "_asset" / provider.provider_entity.icon

        # 5.检测icon是否存在
        if not icon_path.exists():
            raise NotFoundException("该工具提供商_asset下未提供图标")

        # 6.读取icon的类型
        mimetype, _ = mimetypes.guess_type(icon_path)
        mimetype = mimetype or "application/octet-stream"

        # 7.读取icon的字节信息
        with open(icon_path, "rb") as f:
            byte_data = f.read()
            return byte_data, mimetype

    def get_categories(self) -> list[dict[str, Any]]:
        """获取内置提供商的分类信息"""
        category_map = self.builtin_category_manager.get_category_map()
        return [{
            "name": category["entity"].name,
            "category": category["entity"].category,
            "icon": category["icon"]
        } for category in category_map.values()]

    @staticmethod
    def get_tool_inputs(tool) -> list:
        """根据工具函数获取对应的工具传入参数信息"""
        inputs = []
        if hasattr(tool, "args_schema") and issubclass(tool.args_schema, BaseModel):
            for field_name, field_info in tool.args_schema.model_fields.items():
                inputs.append({
                    "name": field_name,
                    "description": field_info.description or "",
                    "required": field_info.is_required(),
                    "type": field_info.annotation.__name__,
                })
        return inputs
