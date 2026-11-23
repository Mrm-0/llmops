#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/8/23 22:19
@Author   :314907015@qq.com
@File     :default_config.py
"""
# 应用默认配置项
DEFAULT_CONFIG = {

    # wtf配置
    "WTF_CSRF_ENABLED": "False",

    # SQLAlchemy数据库配置
    "SQLALCHEMY_DATABASE_URI": "postgresql://postgres:1234@192.168.159.129:5432/llmops",
    "SQLALCHEMY_POOL_SIZE": 30,
    "SQLALCHEMY_POOL_RECYCLE": 3600,
    "SQLALCHEMY_ECHO": "True",

    # Weaviate向量数据库配置
    "WEAVIATE_HTTP_HOST": "localhost",
    "WEAVIATE_HTTP_PORT": 8080,
    "WEAVIATE_CRPC_HOST": "localhost",
    "WEAVIATE_CRPC_PORT": 50051,
    "WEAVIATE_API_KEY": "",

    # Redis数据库配置
    "REDIS_HOST": "localhost",
    "REDIS_PORT": 6379,
    "REDIS_USERNAME": "",
    "REDIS_PASSWORD": "",
    "REDIS_DB": "0",
    "REDIS_USE_SSL": "False",

    # Celery默认配置
    "CELERY_BROKER_DB": 1,
    "CELERY_RESULT_BACKEND_DB": 1,
    "CELERY_TASK_IGNORE_RESULT": "False",
    "CELERY_RESULT_EXPIRES": 3600,
    "CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP": "True",

    # 辅助智能体会话ID
    "ASSISTANT_AGENT_ID": "78e924b6-2174-41c8-9d30-5f27a061350d",
}
