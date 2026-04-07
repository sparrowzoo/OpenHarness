# QueryEngine 类核心总结

QueryEngine 是 OpenHarness 智能体系统的“对话与工具调度核心”，负责维护对话历史、驱动 LLM 交互、调度工具调用，实现了“用户输入-模型推理-工具执行-自动循环”的完整闭环。

## 主要职责
- 维护完整的对话消息链（包括用户输入、模型回复、工具调用结果等）。
- 负责每次用户输入（submit_message）和自动 agent 推理（continue_pending）的主流程调度。
- 通过 run_query 方法与 LLM 进行多轮交互，并根据模型请求自动调用工具，支持并发和多轮 agent loop。
- 记录消耗、支持权限校验、钩子扩展等。

## 关键方法说明
- **submit_message(prompt)**：处理用户主动输入，将输入加入对话历史，驱动主循环（run_query），产出 LLM 回复和工具调用结果。
- **continue_pending(max_turns=None)**：用于自动衔接未完成流程（如 agent 需要多轮推理/自动工具链），不追加新用户输入，直接继续 run_query。
- **run_query(context, messages)**（在 engine/query.py）：底层主循环，负责 LLM 交互、工具调用、并发调度、消息压缩等，是所有智能体推理和自动化的“大脑”。

## 总结
QueryEngine 既是“对话历史的管理者”，也是“智能体推理与工具编排的调度中心”。无论是用户输入还是 agent 自动推进，最终都通过 run_query 方法与 LLM 及工具链路进行交互，实现了灵活、可扩展的智能体主流程。

---
# QueryEngine 源码逐行注释（中文详解）

```python
"""High-level conversation engine."""

from __future__ import annotations

from pathlib import Path
from typing import AsyncIterator

from openharness.api.client import SupportsStreamingMessages
from openharness.engine.cost_tracker import CostTracker
from openharness.engine.messages import ConversationMessage, ToolResultBlock
from openharness.engine.query import AskUserPrompt, PermissionPrompt, QueryContext, run_query
from openharness.engine.stream_events import StreamEvent
from openharness.hooks import HookExecutor
from openharness.permissions.checker import PermissionChecker
from openharness.tools.base import ToolRegistry


class QueryEngine:
	"""拥有对话历史和具备工具感知的模型主循环。"""

	def __init__(
		self,
		*,
		api_client: SupportsStreamingMessages,  # 支持流式消息的API客户端
		tool_registry: ToolRegistry,            # 工具注册表，管理可用工具
		permission_checker: PermissionChecker,  # 权限检查器
		cwd: str | Path,                        # 当前工作目录
		model: str,                             # 使用的模型名
		system_prompt: str,                     # 系统提示词
		max_tokens: int = 4096,                 # 最大token数
		max_turns: int | None = 8,              # 每次用户输入最大agent回合数
		permission_prompt: PermissionPrompt | None = None, # 权限请求回调
		ask_user_prompt: AskUserPrompt | None = None,       # 询问用户回调
		hook_executor: HookExecutor | None = None,          # 钩子执行器
		tool_metadata: dict[str, object] | None = None,     # 工具元数据
	) -> None:
		self._api_client = api_client  # 保存API客户端
		self._tool_registry = tool_registry  # 保存工具注册表
		self._permission_checker = permission_checker  # 保存权限检查器
		self._cwd = Path(cwd).resolve()  # 解析并保存工作目录
		self._model = model  # 保存模型名
		self._system_prompt = system_prompt  # 保存系统提示词
		self._max_tokens = max_tokens  # 保存最大token数
		self._max_turns = max_turns  # 保存最大回合数
		self._permission_prompt = permission_prompt  # 权限请求回调
		self._ask_user_prompt = ask_user_prompt  # 询问用户回调
		self._hook_executor = hook_executor  # 钩子执行器
		self._tool_metadata = tool_metadata or {}  # 工具元数据
		self._messages: list[ConversationMessage] = []  # 对话历史
		self._cost_tracker = CostTracker()  # 费用统计器

	@property
	def messages(self) -> list[ConversationMessage]:
		"""返回当前对话历史。"""
		return list(self._messages)

	@property
	def max_turns(self) -> int | None:
		"""返回每次用户输入允许的最大agent回合数。"""
		return self._max_turns

	@property
	def total_usage(self):
		"""返回所有回合的总消耗。"""
		return self._cost_tracker.total

	def clear(self) -> None:
		"""清空内存中的对话历史。"""
		self._messages.clear()
		self._cost_tracker = CostTracker()

	def set_system_prompt(self, prompt: str) -> None:
		"""更新后续回合的系统提示词。"""
		self._system_prompt = prompt

	def set_model(self, model: str) -> None:
		"""更新后续回合的模型。"""
		self._model = model

	def set_api_client(self, api_client: SupportsStreamingMessages) -> None:
		"""更新后续回合的API客户端。"""
		self._api_client = api_client

	def set_max_turns(self, max_turns: int | None) -> None:
		"""更新每次用户输入的最大agent回合数。"""
		self._max_turns = None if max_turns is None else max(1, int(max_turns))

	def set_permission_checker(self, checker: PermissionChecker) -> None:
		"""更新后续回合的权限检查器。"""
		self._permission_checker = checker

	def load_messages(self, messages: list[ConversationMessage]) -> None:
		"""替换内存中的对话历史。"""
		self._messages = list(messages)

	def has_pending_continuation(self) -> bool:
		"""判断对话是否以工具结果结尾，且需要后续模型回合。"""
		if not self._messages:
			return False
		last = self._messages[-1]
		if last.role != "user":
			return False
		if not any(isinstance(block, ToolResultBlock) for block in last.content):
			return False
		for msg in reversed(self._messages[:-1]):
			if msg.role != "assistant":
				continue
			return bool(msg.tool_uses)
		return False

	async def submit_message(self, prompt: str) -> AsyncIterator[StreamEvent]:
		"""追加一条用户消息并执行主循环。"""
		self._messages.append(ConversationMessage.from_user_text(prompt))  # 加入用户消息
		context = QueryContext(
			api_client=self._api_client,
			tool_registry=self._tool_registry,
			permission_checker=self._permission_checker,
			cwd=self._cwd,
			model=self._model,
			system_prompt=self._system_prompt,
			max_tokens=self._max_tokens,
			max_turns=self._max_turns,
			permission_prompt=self._permission_prompt,
			ask_user_prompt=self._ask_user_prompt,
			hook_executor=self._hook_executor,
			tool_metadata=self._tool_metadata,
		)
		async for event, usage in run_query(context, self._messages):  # 执行主循环
			if usage is not None:
				self._cost_tracker.add(usage)  # 累加消耗
			yield event  # 逐步产出事件

	async def continue_pending(self, *, max_turns: int | None = None) -> AsyncIterator[StreamEvent]:
		"""继续未完成的工具循环，不追加新用户消息。"""
		context = QueryContext(
			api_client=self._api_client,
			tool_registry=self._tool_registry,
			permission_checker=self._permission_checker,
			cwd=self._cwd,
			model=self._model,
			system_prompt=self._system_prompt,
			max_tokens=self._max_tokens,
			max_turns=max_turns if max_turns is not None else self._max_turns,
			permission_prompt=self._permission_prompt,
			ask_user_prompt=self._ask_user_prompt,
			hook_executor=self._hook_executor,
			tool_metadata=self._tool_metadata,
		)
		async for event, usage in run_query(context, self._messages):
			if usage is not None:
				self._cost_tracker.add(usage)
			yield event
```
