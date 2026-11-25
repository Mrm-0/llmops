#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : create_account.py
@Desc    : 创建账号 / 重置密码（项目没有注册接口，首次部署只能手工初始化）

特点：直连 PostgreSQL + 复用 pkg.password 的加密算法，不加载 Flask 应用和 embedding 模型，
      在容器里跑只花 1~2 秒，不会额外吃掉 2G 内存。

用法：

    # ① 脚本已打进镜像（git pull 后 --build 过）
    docker compose exec llmops-api python scripts/create_account.py admin@llmops.dev Admin123456 管理员

    # ② 不想重新构建镜像：从宿主机把脚本喂给容器内的 python（用环境变量传参）
    docker compose exec -T \
        -e ACCOUNT_EMAIL=admin@llmops.dev \
        -e ACCOUNT_PASSWORD=Admin123456 \
        -e ACCOUNT_NAME=管理员 \
        llmops-api python - < ../api/scripts/create_account.py

密码规则：8~16 位，至少包含一个字母和一个数字（与项目 pkg/password 的校验规则一致）。
"""
import argparse
import base64
import os
import secrets
import sys

# 兼容两种执行方式：
#   - python scripts/create_account.py：sys.path[0] 是 scripts/，需要补上项目根目录才能 import pkg
#   - python - < script.py（stdin 模式）：没有 __file__，用当前工作目录（容器里是 /app/api）
if "__file__" in globals():
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
else:
    sys.path.insert(0, os.getcwd())

import psycopg  # noqa: E402

from pkg.password import hash_password, validate_password  # noqa: E402


def get_dsn() -> str:
    """从容器环境变量取连接串，并把 SQLAlchemy 的方言后缀去掉（psycopg 只认 postgresql://）"""
    dsn = os.getenv("SQLALCHEMY_DATABASE_URI", "")
    if not dsn:
        raise SystemExit("环境变量 SQLALCHEMY_DATABASE_URI 未设置，无法连接数据库")
    return (
        dsn.replace("postgresql+psycopg://", "postgresql://")
        .replace("postgresql+psycopg2://", "postgresql://")
    )


def main():
    parser = argparse.ArgumentParser(description="创建账号或重置已有账号的密码")
    parser.add_argument("email", nargs="?", help="登录邮箱")
    parser.add_argument("password", nargs="?", help="登录密码（8-16位，含字母和数字）")
    parser.add_argument("name", nargs="?", default=None, help="显示名称，默认取邮箱 @ 前面的部分")
    args = parser.parse_args()

    email = args.email or os.getenv("ACCOUNT_EMAIL")
    password = args.password or os.getenv("ACCOUNT_PASSWORD")
    name = args.name or os.getenv("ACCOUNT_NAME") or (email.split("@")[0] if email else None)

    if not email or not password:
        parser.error(
            "必须提供 email 和 password（命令行参数，或 ACCOUNT_EMAIL / ACCOUNT_PASSWORD 环境变量）"
        )

    try:
        validate_password(password)
    except ValueError as err:
        raise SystemExit(f"密码不符合规则：{err}")

    # 与 internal/service/account_service.py 的 update_password 完全一致：
    # salt = 16 字节随机数 -> base64；password = base64(hexlify(pbkdf2_hmac('sha256', pwd, salt, 10000)))
    salt = secrets.token_bytes(16)
    password_salt = base64.b64encode(salt).decode()
    password_hashed = base64.b64encode(hash_password(password, salt)).decode()

    with psycopg.connect(get_dsn()) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM account WHERE email = %s LIMIT 1", (email,))
            row = cur.fetchone()

            if row:
                cur.execute(
                    "UPDATE account SET name = %s, password = %s, password_salt = %s, "
                    "updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (name, password_hashed, password_salt, row[0]),
                )
                account_id = row[0]
                action = "已重置密码"
            else:
                cur.execute(
                    "INSERT INTO account (name, email, password, password_salt) "
                    "VALUES (%s, %s, %s, %s) RETURNING id",
                    (name, email, password_hashed, password_salt),
                )
                account_id = cur.fetchone()[0]
                action = "已创建账号"

        conn.commit()

    print(f"{action}：{email}")
    print(f"  账号ID：{account_id}")
    print(f"  显示名：{name}")
    print("  现在可以在登录页用邮箱 + 密码登录了")


if __name__ == "__main__":
    main()
