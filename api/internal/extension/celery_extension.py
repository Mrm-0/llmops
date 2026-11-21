#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/9/28 22:44
@Author   :314907015@qq.com
@File     :celery_extension.py
"""
import dotenv
dotenv.load_dotenv()

from celery import Task, Celery
from flask import Flask


def init_app(app: Flask):
    """初始化Celery配置服务"""

    class FlaskTask(Task):
        """定义FlaskTask，确保Celery在Flask应用的上下文中运行，可以访问flask配置、数据库等内容"""

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    # 1.创建Celery应用并配置
    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config['CELERY'])
    celery_app.set_default()

    # 2.将Celery挂载到app的扩展中
    app.extensions['celery'] = celery_app
