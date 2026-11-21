#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/9/12 17:01
@Author   :314907015@qq.com
@File     :helper.py
"""
import importlib
import random
import string
from _sha3 import sha3_256
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from langchain_core.documents import Document
from pydantic import BaseModel


def dynamic_import(module_name: str, symbol_name: str):
    """动态导入特定模块下的特定功能"""
    module = importlib.import_module(module_name)
    return getattr(module, symbol_name)


def add_attribute(attr_name: str, attr_value: Any):
    def decorator(func):
        setattr(func, attr_name, attr_value)
        return func

    return decorator


def generate_text_hash(text: str) -> str:
    """根据传递的文本计算对应的哈希值"""
    # 1.将需要计算哈希值的内容加上None字符串，避免传递了空字符串导致计算出错
    text = str(text) + "None"

    # 2.使用sha3_256将数据转换成哈希值后返回
    return sha3_256(text.encode()).hexdigest()


def datetime_to_timestamp(dt: datetime):
    """将传入的datetime时间转换为时间戳"""
    if dt is None:
        return 0
    return int(dt.timestamp())


def combine_documents(documents: list[Document]) -> str:
    """将对应的文档列表使用换行符进行合并"""
    return "\n\n".join([document.page_content for document in documents])


def remove_fields(data_dict: dict, fields: list[str]) -> None:
    """根据传递的字段列表，移除字典中的指定字段"""
    for field in fields:
        data_dict.pop(field, None)


def convert_model_to_dict(obj: Any, *args, **kwargs):
    """辅助函数，将Pydantic V1版本中的UUID/Enum等数据转换成可序列化存储的数据。"""
    # 1.如果是Pydantic的BaseModel类型，递归处理其字段
    if isinstance(obj, BaseModel):
        obj_dict = obj.model_dump(*args, **kwargs)
        # 2.递归处理嵌套字段
        for key, value in obj_dict.items():
            obj_dict[key] = convert_model_to_dict(value, *args, **kwargs)
        return obj_dict

    # 3.如果是 UUID 类型，转换为字符串
    elif isinstance(obj, UUID):
        return str(obj)

    # 4.如果是 Enum 类型，转换为其值
    elif isinstance(obj, Enum):
        return obj.value

    # 5.如果是列表类型，递归处理列表中的每个元素
    elif isinstance(obj, list):
        return [convert_model_to_dict(item, *args, **kwargs) for item in obj]

    # 6.如果是字典类型，递归处理字典中的每个字段
    elif isinstance(obj, dict):
        return {key: convert_model_to_dict(value, *args, **kwargs) for key, value in obj.items()}

    # 7.对其他类型的字段，保持原样
    return obj


def get_value_type(value: Any) -> Any:
    """根据传递的值获取变量类型，并将str和bool转换成string和boolean"""
    # 1.计算变量类型并转换成字符串
    type_value = type(value).__name__

    # 2.判断是否为str或bool
    if type_value == "str":
        return "string"
    elif type_value == "bool":
        return "boolean"

    return type_value


def generate_random_string(length: int = 16) -> str:
    """根据传递的位数，生成随机字符串"""
    # 1.定义字符集，包含字母大小写和数字
    chars = string.ascii_letters + string.digits

    # 2.使用random.choices生成指定长度的随机字符串
    random_str = ''.join(random.choices(chars, k=length))

    return random_str
