#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/10/28 16:38
@Author   :314907015@qq.com
@File     :oauth_handler.py
"""
from dataclasses import dataclass

from injector import inject

from internal.schema.oauth_schema import AuthorizeReq, AuthorizeResp
from internal.service import OAuthService
from pkg.response import success_json, validate_error_json


@inject
@dataclass
class OAuthHandler:
    """第三方授权服务类"""
    oauth_service: OAuthService

    def provider(self, provider_name: str):
        """根据传递的提供商名字获取授权认证重定向地址"""
        # 1.根据提供的provider_name获取提供商实例
        oauth = self.oauth_service.get_oauth_by_provider_name(provider_name)

        # 2.调用类函数获取地址
        redirect_uri = oauth.get_authorization_url()

        # 3.返回给前端时字段名必须是 redirect_url（与前端 use-oauth.ts / models/oauth.ts 保持一致，
        # 前端读的是 resp.data.redirect_url）。写成 redirect_uri 会导致前端拿到 undefined，
        # window.location.href = undefined，表现为点击第三方登录"没有任何反应"
        return success_json({"redirect_url": redirect_uri})

    def authorize(self, provider_name: str):
        """根据传递的提供商名字+code获取第三方授权信息"""
        # 1.提取请求并校验
        req = AuthorizeReq()
        if not req.validate():
            raise validate_error_json(req.errors)

        # 2.调用服务登录账号
        credential = self.oauth_service.oauth_login(provider_name, req.code.data)

        return success_json(AuthorizeResp().dump(credential))
