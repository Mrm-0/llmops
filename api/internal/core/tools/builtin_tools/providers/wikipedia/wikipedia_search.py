#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/9/13 20:48
@Author   :314907015@qq.com
@File     :wikipedia_search.py
"""

from langchain_community.tools import WikipediaQueryRun
from langchain_community.tools.wikipedia.tool import WikipediaQueryInput
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import BaseTool

from internal.lib.helper import add_attribute


@add_attribute("args_schema",WikipediaQueryInput)
def wikipedia_search(**kwargs) -> BaseTool:
    """返回维基百科搜索工具"""
    return WikipediaQueryRun(
        api_wrapper=WikipediaAPIWrapper(
            lang='zh',
        ),
    )
