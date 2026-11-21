#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/9/27 22:01
@Author   :314907015@qq.com
@File     :logging_extension.py
"""
import logging
import os
import sys

from concurrent_log_handler import ConcurrentTimedRotatingFileHandler
from flask import Flask


def init_app(app: Flask):
    """日志记录器初始化"""
    # 1.根据不同的环境设置logging根处理器的日志级别
    logging.getLogger().setLevel(
        logging.DEBUG if app.debug or os.getenv('FLASK_ENV') == 'development' else logging.WARNING
    )
    # 2.设置日志存放的文件位置，不存在则创建
    log_folder = os.path.join(os.getcwd(), 'storage', 'logs')
    if not os.path.exists(log_folder):
        os.mkdir(log_folder)

    # 3.定义日志的文件名
    log_file = os.path.join(log_folder, 'app.log')

    # 4.设置日志的格式，并每天更新一次

    handler = ConcurrentTimedRotatingFileHandler(
        log_file,
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8',
    )
    formatter = logging.Formatter(
        '[%(asctime)s.%(msecs)03d] %(filename)s -> %(funcName)s line:%(lineno)d [%(levelname)s]: %(message)s',
    )
    handler.setLevel(logging.DEBUG if app.debug or os.getenv('FLASK_ENV') == 'development' else logging.WARNING)
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

    # 5.在开发环境下同时将日志输出到控制台
    if app.debug or os.getenv('FLASK_ENV') == 'development':
        # Windows 控制台默认 GBK，遇到 emoji 等字符会抛 UnicodeEncodeError 导致整条日志丢失，
        # 这里把标准输出统一切到 utf-8，并允许无法编码的字符转义输出而不是抛异常
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
            sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
        except (AttributeError, ValueError):
            pass
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)
