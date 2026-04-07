# print_context_plugin 插件说明

本插件用于 OpenHarness，作用是在每次 tool 被调用前（pre_tool_use 阶段）自动打印完整的上下文信息，便于调试和能力编排分析。

## 目录结构

```
plugins/
  print_context_plugin/
    hooks/
      hooks.json
    print_context_hook.py
    README.md
```

## hooks.json 配置

```json
{
  "pre_tool_use": [
    {
      "type": "python",
      "module": "plugins.print_context_plugin.print_context_hook",
      "function": "print_context_hook",
      "matcher": "*"
    }
  ]
}
```

- type: python 代表调用 Python 函数
- module/function: 指定钩子实现
- matcher: "*" 代表所有 tool/skill/agent 均生效

## 钩子实现 print_context_hook.py

```python
def print_context_hook(context):
    import json
    print("\n==== [print_context_plugin] pre_tool_use context dump ====")
    print(json.dumps(context, indent=2, ensure_ascii=False))
    print("==== [print_context_plugin] end ====")
    return context
```

## 使用说明
1. 将本插件目录放入 OpenHarness 的 plugins/ 目录下
2. 启动 OpenHarness，调用任意 tool/skill/agent 时，终端会自动打印完整上下文
3. 适合调试、能力编排分析、插件开发等场景

---
如需定制 matcher 或扩展其它事件，请修改 hooks.json 配置。
