#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/9/15 16:53
@Author   :314907015@qq.com
@File     :category_entity.py
"""
from pydantic import BaseModel, field_validator
from internal.exception import FailException


class CategoryEntity(BaseModel):
    """分类实体"""
    category: str  # 分类唯一标识
    name: str  # 分类名称
    icon: str  # 分类图标名称

    @field_validator("icon")
    @classmethod
    def check_icon_extension(cls, value: str):
        """检测icon的扩展名是否为svg，不是则抛出错误"""
        if not value.endswith('.svg'):
            raise FailException("该分类的扩展图标不是.svg格式")
        return value
