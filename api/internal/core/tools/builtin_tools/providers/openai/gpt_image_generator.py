#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/9/13 20:03
@Author   :314907015@qq.com
@File     :gpt_image_generator.py
"""
from typing import Any

from dotenv import load_dotenv
from langchain_core.tools import BaseTool
from openai import OpenAI
from pydantic import BaseModel, Field

from internal.lib.helper import add_attribute

load_dotenv()


# 1. 定义工具调用参数 schema（给调用方/大模型看的输入规范）
class ImageGenerationArgs(BaseModel):
    prompt: str = Field(description="图片生成的文本描述，越详细生成效果越好")
    size: str = Field(default="1024x1024", description="图片尺寸,支持1024x1024/1792x1024/1024x1792")


# 2. 工具实现类
class GPTImageGenerationTool(BaseTool):
    # 工具元信息
    name: str = "gpt_image_generator"
    description: str = "GPT图片生成工具，根据文本描述生成图片，返回base64编码的图片数据"
    args_schema: type[BaseModel] = ImageGenerationArgs  # 绑定输入参数模型

    # 工具配置参数（初始化时传入，运行时不变）
    image_model: str = "gpt-image-2"
    client: OpenAI = Field(default_factory=OpenAI)

    def _run(self, prompt: str, size: str | None = None, **kwargs: Any) -> str:
        """执行图片生成"""
        # 没传 size 就用模型默认尺寸
        use_size = size or "1024x1024"

        response = self.client.images.generate(
            model=self.image_model,
            prompt=prompt,
            size=use_size,
            quality="high",
            response_format="b64_json"
        )
        # 返回 base64 字符串
        return response.data[0].b64_json


# 3. 工厂函数
@add_attribute("args_schema", ImageGenerationArgs)
def gpt_image_generator(**kwargs) -> BaseTool:
    return GPTImageGenerationTool(**kwargs)


# 测试调用
if __name__ == "__main__":
    tool = gpt_image_generator()
    # 推荐用字典传参，语义清晰；也支持 invoke("画一张卡通猫的图片") 位置参数写法
    base64_img = tool.invoke({"prompt": "画一张卡通猫的图片", "size": "1024x1024"})
    print(f"生成成功，base64长度：{len(base64_img)}")
