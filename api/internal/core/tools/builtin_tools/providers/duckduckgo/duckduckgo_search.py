#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/9/13 13:57
@Author   :314907015@qq.com
@File     :duckduckgo_search.py
"""
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from internal.lib.helper import add_attribute


class DDGInput(BaseModel):
    query: str = Field(description="需要搜索的查询语句")


@add_attribute("args_schema", DDGInput)
def duckduckgo_search(**kwargs) -> BaseTool:
    """返回DuckDuckGo搜索工具"""
    from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
    return DuckDuckGoSearchRun(
        description="一个注重隐私的搜索工具，当你需要搜索实时时可以使用该工具，工具输入是一个查询语句",
        args_schema=DDGInput,
        api_wrapper=DuckDuckGoSearchAPIWrapper(
            backend="auto"
        ),
    )
