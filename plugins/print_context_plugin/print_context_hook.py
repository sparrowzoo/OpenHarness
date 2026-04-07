"""
OpenHarness 插件示例：打印 pre_tool_use 阶段的完整上下文信息
文件路径：plugins/print_context_plugin/print_context_hook.py
"""

def print_context_hook(context):
    """
    打印 tool 调用前的完整上下文信息。
    :param context: OpenHarness 传入的上下文 dict，包含 tool/skill/agent/参数/用户等全部信息
    """
    import json
    print("\n==== [print_context_plugin] pre_tool_use context dump ====")
    print(json.dumps(context, indent=2, ensure_ascii=False))
    print("==== [print_context_plugin] end ====")
    # 可选：返回 context 不做修改
    return context
