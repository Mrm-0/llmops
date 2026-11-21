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

        return success_json({"redirect_uri": redirect_uri})

    def authorize(self, provider_name: str):
        """根据传递的提供商名字+code获取第三方授权信息"""
        # 1.提取请求并校验
        req = AuthorizeReq()
        if not req.validate():
            raise validate_error_json(req.errors)

        # 2.调用服务登录账号
        credential = self.oauth_service.oauth_login(provider_name, req.code.data)

        return success_json(AuthorizeResp().dump(credential))
