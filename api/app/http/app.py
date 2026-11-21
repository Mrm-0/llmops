#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/8/21 16:56
@Author   :314907015@qq.com
@File     :app.py
"""
import os

import dotenv

# 将env加载到环境变量中
dotenv.load_dotenv()

# 1.为开发环境配置猴子补丁
if os.environ.get("FLASK_ENV") == "production" or os.environ.get("FLASK_DEBUG") == 0:
    from gevent import monkey

    monkey.patch_all()

    import grpc.experimental.gevent

    grpc.experimental.gevent.init_gevent()

from flask_login import LoginManager
from flask_migrate import Migrate
from flask_weaviate import FlaskWeaviate

from config import Config
from internal.middleware import Middleware
from internal.router import Router
from internal.server import Http
from pkg.sqlalchemy import SQLAlchemy
from .module import injector

conf = Config()

# 实例化服务引擎
app = Http(
    __name__,
    conf=conf,
    weaviate=injector.get(FlaskWeaviate),
    migrate=injector.get(Migrate),
    login_manager=injector.get(LoginManager),
    middleware=injector.get(Middleware),
    db=injector.get(SQLAlchemy),
    router=injector.get(Router),
)

celery = app.extensions['celery']

if __name__ == "__main__":
    app.run(debug=True)
