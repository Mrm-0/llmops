#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/10/22 22:30
@Author   :314907015@qq.com
@File     :base_agent.py
"""
import logging
import threading
import uuid
from abc import abstractmethod
from typing import Any, Iterator

from langchain_core.load import Serializable
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from pydantic import ConfigDict, PrivateAttr

from internal.core.agent.agents.agent_queue_manager import AgentQueueManager
from internal.core.agent.entities.agent_entity import AgentConfig, AgentState
from internal.core.agent.entities.queue_entity import AgentResult, QueueEvent, AgentThought
from internal.core.language_model.entities.model_entity import BaseLanguageModel
from internal.exception import FailException


class BaseAgent(Serializable, Runnable):
    """基于Runnable的基础智能体基类"""
    # Runnable 上声明了 name: str | None 但没有默认值，pydantic v2 会将其视为必填字段，
    # 因此这里必须显式给出默认值，否则实例化时会报 "name Field required"
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str | None = None
    llm: BaseLanguageModel
    agent_config: AgentConfig
    _agent: CompiledStateGraph = PrivateAttr(None)
    _agent_queue_manager: AgentQueueManager = PrivateAttr(None)

    def __init__(
            self,
            llm: BaseLanguageModel,
            agent_config: AgentConfig,
            *args,
            **kwargs
    ):
        """初始化智能体图结构程序"""
        super().__init__(*args, llm=llm, agent_config=agent_config, **kwargs)
        self._agent = self._built_agent()
        self._agent_queue_manager = AgentQueueManager(
            user_id=agent_config.user_id,
            invoke_from=agent_config.invoke_from,
        )

    @abstractmethod
    def _built_agent(self) -> CompiledStateGraph:
        """构建智能体函数，等待子类实现"""
        raise NotImplementedError("_built_agent()未实现")

    def invoke(
            self,
            input: AgentState,
            config: RunnableConfig | None = None,
            **kwargs: Any,
    ) -> AgentResult:
        """块内容响应，一次性生成完整内容后返回"""
        # 1.调用stream方法获取流式事件输出数据
        content = input["messages"][0].content
        query = ""
        image_urls = []
        if isinstance(content, str):
            query = content
        elif isinstance(content, list):
            query = content[0]["text"]
            image_urls = [chunk["image_url"]["url"] for chunk in content if chunk.get("type") == "image_url"]
        agent_result = AgentResult(query=query, image_urls=image_urls)
        agent_thoughts = {}
        for agent_thought in self.stream(input, config):
            # 2.提取事件id并转换成字符串
            event_id = str(agent_thought.id)

            # 3.除了ping事件，其他事件都记录
            if agent_thought.event != QueueEvent.PING:
                # 4.单独叠加处理agent_message事件
                if agent_thought.event == QueueEvent.AGENT_MESSAGE:
                    # 5.检测是否已经存储了事件
                    if event_id not in agent_thoughts:
                        # 6.初始化智能体消息
                        agent_thoughts[event_id] = agent_thought
                    else:
                        # 7.叠加智能体消息事件
                        agent_thoughts[event_id] = agent_thoughts[event_id].model_copy(update={
                            "thought": agent_thoughts[event_id].thought + agent_thought.thought,
                            "answer": agent_thoughts[event_id].answer + agent_thought.answer,
                            "latency": agent_thought.latency,
                        })
                    # 8.更新智能体消息答案
                    agent_result.answer += agent_thought.answer
                else:
                    # 9.其他类型事件均覆盖
                    agent_thoughts[event_id] = agent_thought

                    # 10.判断是否为异常消息类型，是则修改状态并记录错误
                    if agent_thought.event in [QueueEvent.STOP, QueueEvent.TIMEOUT, QueueEvent.ERROR]:
                        agent_result.status = agent_thought.event
                        agent_result.error = agent_thought.observation if agent_thought.event == QueueEvent.ERROR else ""

        # 11.将推理字典转换成列表并储存
        agent_result.agent_thoughts = [agent_thought for agent_thought in agent_thoughts.values()]

        # 12.完善message
        agent_result.message = next(
            (agent_thought.message for agent_thought in agent_thoughts.values()
             if agent_thought.event == QueueEvent.AGENT_MESSAGE),
            []
        )

        # 13.更新总耗时
        agent_result.latency = sum([agent_thought.latency for agent_thought in agent_thoughts.values()])

        return agent_result

    def stream(
            self,
            input: AgentState,
            config: RunnableConfig | None = None,
            **kwargs: Any | None,
    ) -> Iterator[AgentThought]:
        """流式输出，每个Not节点或者LLM每生成一个token时则返回相应的内容"""
        # 1.检测子类是否构建了Agent智能体，为构建则抛出错误
        if not self._agent:
            raise FailException("智能体未成功构建，请核实后重试")

        # 2.构建对应的任务id以及数据初始化
        input['task_id'] = input.get('task_id', uuid.uuid4())
        input['history'] = input.get('history', [])
        input['iteration_count'] = input.get('iteration_count', 0)
        input['long_term_memory'] = input.get('long_term_memory', "")

        # 3.启动线程前同步预创建队列，消除监听线程与工作线程的创建竞态
        self._agent_queue_manager.queue(input['task_id'])

        # 4.创建子线程并执行（带异常兜底，避免线程静默死亡导致SSE挂死）
        def _run() -> None:
            try:
                self._agent.invoke(input)
            except Exception as e:
                logging.exception("智能体执行出错")
                self._agent_queue_manager.publish_error(input['task_id'], f"智能体执行出错: {str(e)}")

        thread = threading.Thread(
            target=_run,
            daemon=True,
        )
        thread.start()

        # 5.调用队列管理器监听数据并返回迭代器
        yield from self._agent_queue_manager.listen(input['task_id'])

    @property
    def agent_queue_manager(self) -> AgentQueueManager:
        """只读属性，返回智能体队列管理器"""
        return self._agent_queue_manager
