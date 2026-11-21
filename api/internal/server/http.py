#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/8/21 16:43
@Author   :314907015@qq.com
@File     :http.py
"""
import logging
import os

from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_weaviate import FlaskWeaviate

from config import Config
from internal.exception import CustomException
from internal.extension import logging_extension, redis_extension, celery_extension
from internal.middleware import Middleware
from internal.router import Router
from pkg.response import json, Response, HttpCode
from pkg.sqlalchemy import SQLAlchemy


class Http(Flask):
    """Http服务引擎"""

    def __init__(
            self,
            *args,
            conf: Config,
            weaviate:FlaskWeaviate,
            migrate: Migrate,
            login_manager: LoginManager,
            # 中间件
            middleware: Middleware,
            db: SQLAlchemy,
            router: Router,
            **kwargs
    ):
        super().__init__(*args, **kwargs)

        # 1.初始化应用配置
        self.config.from_object(conf)

        # 2，注册绑定异常错误处理
        self.register_error_handler(Exception, self._register_error_handler)

        # 3.初始化flask扩展
        db.init_app(self)
        weaviate.init_app(self)
        migrate.init_app(self, db, directory="internal/migration")
        redis_extension.init_app(self)
        celery_extension.init_app(self)
        logging_extension.init_app(self)
        login_manager.init_app(self)

        # 4.解决前后端跨域问题
        CORS(self, resources={
            r'/*': {
                "origins": "*",
                "supports_credentials": True,
                # "methods":["GET","POST"],
                # "allow_headers":["Content-Type"],
            }
        })

        # 5.注册中间件应用
        login_manager.request_loader(middleware.request_loader)

        # 6.注册应用路由
        router.register_router(self)

    def _register_error_handler(self, error: Exception):
        # 1.日志记录异常信息
        logging.error("接口发生未捕获异常,error:%(error)s", {"error": error}, exc_info=True)

        # 2.自定义异常，可以提取message，data等信息
        if isinstance(error, CustomException):
            return json(Response(
                code=error.code,
                message=error.message,
                data=error.data if error.data is not None else {},
            ))

        # 3.不是自定义异常，可能是数据库、程序提出的异常，也可以提取信息，设置FAIL状态码
        if self.debug or os.getenv("FLASK_ENV") == "development":
            raise error
        else:
            return json(Response(
                code=HttpCode.FAIL,
                message=str(error),
                data={},
            ))
