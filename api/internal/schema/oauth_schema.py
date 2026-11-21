#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/10/28 17:12
@Author   :314907015@qq.com
@File     :oauth_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired


class AuthorizeReq(FlaskForm):
    """第三方授权认证请求体"""
    code = StringField('code', validators=[DataRequired("code代码不能为空")])


class AuthorizeResp(Schema):
    """第三方授权认证响应体"""
    access_token = fields.Str()
    expire_at = fields.Int()
