#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/9/17 17:37
@Author   :314907015@qq.com
@File     :schema.py
"""
from wtforms import Field


class ListField(Field):
    """自定义List字段，用于储存列表型数据"""
    data: list = None

    def process_formdata(self, valuelist):
        if valuelist is not None and isinstance(valuelist, list):
            self.data = valuelist

    def _value(self):
        return self.data if self.data is not None else []


class DictField(Field):
    """自定义Dict字段"""
    data: dict = None

    def process_formdata(self, valuelist):
        if valuelist is not None and len(valuelist) > 0 and isinstance(valuelist[0], dict):
            self.data = valuelist[0]

    def _value(self):
        return self.data
