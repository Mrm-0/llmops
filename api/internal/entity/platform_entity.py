#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/11/24 21:08
@Author   :314907015@qq.com
@File     :platform_entity.py
"""
from enum import Enum


class WechatConfigStatus(str, Enum):
    """微信配置状态"""
    CONFIGURED = "configured"  # 已配置
    UNCONFIGURED = "unconfigured"  # 未配置