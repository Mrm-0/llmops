#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/9/15 16:39
@Author   :314907015@qq.com
@File     :builtin_category_manager.py
"""
from typing import Any
from pathlib import Path
import yaml
from injector import inject, singleton
from pydantic import BaseModel, Field
from internal.core.tools.builtin_tools.entities import CategoryEntity
from internal.exception import NotFoundException


@inject
@singleton
class BuiltinCategoryManager(BaseModel):
    """内置工具分类管理器"""
    category_map: dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **kwargs):
        """分类管理器初始化"""
        super().__init__(**kwargs)
        self._init_categories()

    def get_category_map(self) -> dict[str, Any]:
        """获取分类映射信息"""
        return self.category_map

    def _init_categories(self):
        """初始化分类数据"""
        # 1.检测数据是否已经处理
        if self.category_map:
            return

        # 2.获取yaml数据
        category_path = Path(__file__).parent
        category_yaml_path = category_path / "categories.yaml"
        with open(category_yaml_path, encoding="utf-8") as f:
            categories = yaml.safe_load(f)

        # 3.遍历所有分类数据，并且将分类加载为实体信息
        for category in categories:
            # 4.创建分类的实体
            category_entity = CategoryEntity(**category)

            # 5.获取icon位置，并检测icon是否存在
            icon_path = category_path / "icons" / category["icon"]
            if not icon_path.exists():
                raise NotFoundException(f"该分类{category_entity.category}的icon未提供")

            # 6.读取对应的icon信息
            with open(icon_path, encoding="utf-8") as f:
                icon = f.read()

            # 7.将数据映射到字典中
            self.category_map[category_entity.category] = {
                "entity": category_entity,
                "icon": icon,
            }
