#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/9/13 13:38
@Author   :314907015@qq.com
@File     :current_time.py
"""
from datetime import datetime
from typing import Any, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel


class CurrentTime(BaseTool):
    """一个用于获取当前时间的工具"""
    name: str = "current_time"
    description: str = "一个用于获取当前时间的工具"
    args_schema: Type[BaseModel] = BaseModel

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """获取当前系统的时间并格式化返回"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")


def current_time(**kwargs) -> BaseTool:
    """返回获取当前时间的langchain工具"""
    return CurrentTime()
