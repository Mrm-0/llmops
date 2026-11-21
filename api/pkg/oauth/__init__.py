#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/10/27 18:43
@Author   :314907015@qq.com
@File     :__init__.py.py
"""
from .github_oauth import GithubOAuth
from .oauth import OAuthUserInfo, OAuth

__all__ = ["OAuth", "OAuthUserInfo", GithubOAuth]
