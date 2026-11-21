#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/11/17 16:58
@Author   :314907015@qq.com
@File     :cogview_image_generator.py
"""
import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.tools import BaseTool
from openai import OpenAI
from pydantic import BaseModel, Field

from internal.lib.helper import add_attribute

load_dotenv()


# 1. 定义工具调用参数 schema（给调用方/大模型看的输入规范）
class CogViewGenerationArgs(BaseModel):
    prompt: str = Field(description="图片生成的文本描述，越详细生成效果越好")
    size: str = Field(default="1024x1024",
                      description="图片尺寸,支持1024x1024/1344x768/768x1344/1152x864/864x1152/1440x720/720x1440")


# 2. 工具实现类
class CogViewGenerationTool(BaseTool):
    # 工具元信息
    name: str = "cogview_image_generator"
    description: str = "智谱CogView生图工具，根据文本描述生成图片，返回图片URL"
    args_schema: type[BaseModel] = CogViewGenerationArgs  # 绑定输入参数模型

    # 工具配置参数（初始化时传入，运行时不变）
    # client 不设默认值，强制由工厂函数显式注入指向智谱的客户端，
    # 避免 OpenAI() 默认构造时静默读取 OPENAI_API_KEY/OPENAI_BASE_URL
    image_model: str = "cogview-4"
    client: OpenAI

    def _run(self, prompt: str, size: str | None = None, **kwargs: Any) -> str:
        """执行图片生成，返回图片URL"""
        # 没传 size 就用默认尺寸
        use_size = size or "1024x1024"

        # 智谱 images 接口兼容 OpenAI SDK 协议，直接调用 generate
        # 注意：CogView-4 不支持 quality/response_format 等参数，不要传递
        response = self.client.images.generate(
            model=self.image_model,
            prompt=prompt,
            size=use_size,
        )
        # 返回图片URL
        return response.data[0].url


# 3. 工厂函数
@add_attribute("args_schema", CogViewGenerationArgs)
def cogview_image_generator(**kwargs) -> BaseTool:
    # 密钥显式注入，避免 OpenAI SDK 静默回读 OPENAI_API_KEY
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        raise ValueError("请在 .env 中配置 ZHIPU_API_KEY 后再使用智谱生图工具")

    kwargs.setdefault("client", OpenAI(api_key=api_key, base_url="https://open.bigmodel.cn/api/paas/v4"))
    return CogViewGenerationTool(**kwargs)


# 测试调用
if __name__ == "__main__":
    tool = cogview_image_generator()
    # 推荐用字典传参，语义清晰；也支持 invoke("画一张卡通猫的图片") 位置参数写法
    img_url = tool.invoke({"prompt": "画一张卡通猫的图片", "size": "1024x1024"})
    print(f"生成成功，图片URL：{img_url}")
