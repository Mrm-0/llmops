#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/8/21 23:26
@Author   :314907015@qq.com
@File     :config.py
"""
import os
from typing import Any

from config.default_config import DEFAULT_CONFIG


def _get_env(key: str) -> Any:
    """从环境变量中获取配置项，如果找不到则返回默认值"""
    return os.getenv(key, DEFAULT_CONFIG.get(key))


def _get_bool_env(key: str) -> bool:
    """从环境变量中获取布尔值型配置项，如果找不到则返回默认值"""
    value: str = _get_env(key)
    return value.lower() == "true" if value is not None else False


class Config:
    def __init__(self):
        # 关闭wtf的csrf保护
        self.WTF_CSRF_ENABLED = _get_bool_env("WTF_CSRF_ENABLED")

        # 数据库配置
        self.SQLALCHEMY_DATABASE_URI = _get_env("SQLALCHEMY_DATABASE_URI")
        self.SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_size": int(_get_env("SQLALCHEMY_POOL_SIZE")),
            "pool_recycle": int(_get_env("SQLALCHEMY_POOL_RECYCLE")),
            # 取连接前先探活，避免拿到被服务端回收的失效连接（配合 pool_recycle 使用）
            "pool_pre_ping": True,
        }
        self.SQLALCHEMY_ECHO = _get_bool_env("SQLALCHEMY_ECHO")

        # Weaviate向量数据库配置
        # 注意: flask_weaviate 只识别 WEAVIATE_GRPC_HOST / WEAVIATE_GRPC_PORT 这组 key,
        #       之前写成 CRPC/WEAVAITE 导致容器内 gRPC 回退到 localhost, 向量库连不上
        self.WEAVIATE_HTTP_HOST = _get_env("WEAVIATE_HTTP_HOST")
        self.WEAVIATE_HTTP_PORT = int(_get_env("WEAVIATE_HTTP_PORT"))
        self.WEAVIATE_GRPC_HOST = _get_env("WEAVIATE_GRPC_HOST")
        self.WEAVIATE_GRPC_PORT = int(_get_env("WEAVIATE_GRPC_PORT"))
        self.WEAVIATE_API_KEY = _get_env("WEAVIATE_API_KEY")

        # Redis配置
        self.REDIS_HOST = _get_env("REDIS_HOST")
        self.REDIS_PORT = _get_env("REDIS_PORT")
        self.REDIS_USERNAME = _get_env("REDIS_USERNAME")
        self.REDIS_PASSWORD = _get_env("REDIS_PASSWORD")
        self.REDIS_DB = _get_env("REDIS_DB")
        self.REDIS_USE_SSL = _get_bool_env("REDIS_USE_SSL")

        # Celery配置
        self.CELERY = {
            "broker_url": f"redis://{self.REDIS_USERNAME}:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{int(_get_env("CELERY_BROKER_DB"))}",
            "result_backend": f"redis://{self.REDIS_USERNAME}:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{int(_get_env("CELERY_RESULT_BACKEND_DB"))}",
            "task_ignore_result": _get_bool_env("CELERY_TASK_IGNORE_RESULT"),
            "result_expires": int(_get_env("CELERY_RESULT_EXPIRES")),
            "broker_connection_retry_on_startup": _get_bool_env("CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP"),
        }

        # 辅助Agent应用标识id
        self.ASSISTANT_AGENT_ID = _get_env("ASSISTANT_AGENT_ID")
