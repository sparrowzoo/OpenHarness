
---
# OpenHarness 能力体系权威总结

## 1. subagent、skill、tool 的本质与关系

### 权威定义

- **tool**：能力的最小实现单元，通常绑定具体实现（如本地 API、脚本、插件等），协议为私有协议，参数和调用方式由实现方决定。
- **skill**：基于 MCP（Model Context Protocol）协议的能力描述，强调标准化、跨平台和可组合性，便于不同系统间能力复用和编排。
- **subagent**：对 tool/skill 的进一步组织和分层，相当于“能力代理”或“能力调度者”，根据任务类型、领域、上下文等对底层 tool/skill 进行分门别类和智能调度。

### 关系与作用

1. **tool 与 skill 的关系**
   - 本质都是“能力”的抽象和封装。
   - tool 偏向本地/私有实现，skill 偏向标准化和跨平台。
   - skill 可以包装 tool，提供统一协议和更强的组合能力。

2. **subagent 的意义**
   - 没有 subagent 时，LLM 需要在所有 tool/skill 里盲目检索，效率低且容易出错。
   - subagent 像“目录”一样分层管理能力，提升推理和调用的准确性。
   - subagent 负责将 tool/skill 按领域、任务、上下文等分门别类，便于 LLM 智能分析和调用。

3. **三者协同提升智能化水平**
   - tool/skill 提供底层能力，subagent 负责智能编排和调度。
   - 共同提升 LLM 的可用性、扩展性和智能化水平。

#### 总结

- skill 和 tool 的本质都是能力的不同协议封装，subagent 是对能力的智能编排和分层。
- subagent、skill、tool 三者共同构建了高效、可扩展、智能化的 AI 能力调用体系。

> 例子：
> - 没有 subagent 时，LLM 相当于“大海捞针”；有了 subagent，相当于有了“目录”和“分类”，大大提升了检索和调用效率。
> - skill 是标准协议能力，tool 是本地实现能力，subagent 是能力的智能调度者。

---
## 2. harness、permissions、hook 的本质与 AOP 类比

- **harness**：本质是对 tool 调用的“包裹器”或“执行环境”。它在 tool 执行前后，自动运行本地程序（如前置/后置校验、日志、mock、数据转换等），对 tool 的入参和出参进行规范、校验、转换或限制，确保调用过程可控、可观测、可扩展。
   - harness 让 tool 的调用更安全、标准化、可插拔。
   - harness 可以实现自动化测试、mock、限流、审计等功能。

- **permissions**：本质是特殊的 hook，专门用于权限校验。它在 tool 或 skill 被调用前，判断当前上下文是否有权访问该能力，决定是否放行或拒绝调用。
   - permissions 通常以 hook 形式嵌入 harness 或 agent 调度流程中。
   - 典型场景如：用户身份校验、敏感操作拦截、合规性检查等。

- **hook**：通用的“钩子”机制，允许在能力调用的各个阶段（如前置、后置、异常等）插入自定义逻辑。permissions 只是 hook 的一种，harness 也常用 hook 实现扩展。

### hook 与 plugin 的本质关系与最佳理解方式

- **hook（钩子）** 是框架预定义的“插座”，在能力调用生命周期的关键节点（如 pre_tool_use、post_tool_use、session_start 等）暴露回调点，允许插入自定义逻辑。
- **plugin（插件）** 是“插头”，负责实现具体的 hook 逻辑。插件可以批量注册多个 hook，也可以注册 tool、skill、agent 等能力。
- hook 回调时会传递丰富的上下文（如当前 tool、输入参数、用户、环境等），plugin 可以根据上下文和全局/本地配置灵活决定是否执行、如何执行具体逻辑。
- 这种设计实现了“框架预埋插座 + 插件灵活插拔 + 上下文驱动决策”，极大提升了系统的可扩展性和可插拔性。

#### 正确理解

- hook 是扩展点（插座），plugin 是扩展实现（插头），上下文和配置决定了“插头”是否以及如何响应“插座”的调用。
- 切面（AOP）类比在 OpenHarness 中并非严格基于 tool 或 plugin，而是基于“事件驱动+能力注册”体系下的横切关注点实现。hook 是切面的载体，plugin 是切面的批量分发者，tool/skill/agent 是被切面的对象。
- 插件让切面批量化、可组合、可复用，但切面本身的生效范围和粒度是可配置和可编排的。

#### 最佳实践建议

- 设计切面时，优先考虑事件（如 pre_tool_use、post_tool_use、session_start 等）和能力类型（tool/skill/agent）。
- 用插件批量分发 hook，但用 matcher 或配置精细控制 hook 的作用范围。
- 保持 hook 逻辑解耦、可插拔，避免单一插件/能力耦合过重。

#### 总结

- harness = tool 的“执行环境”+“前后处理”+“本地流程编排”
- permissions = 特殊的 hook，专注于权限控制
- hook = 插拔式扩展点，贯穿 harness、agent、tool 调用全流程

三者共同构建了安全、可控、可扩展的 AI 能力调用体系，其思想与 AOP 十分契合。

---

### 全局与插件级 hooks 配置的本质区别

> **配置决定的是“插件/钩子在哪块（哪些能力/事件）执行”，不是“某块能力可以选择性加载哪些插件”**。

OpenHarness 的 hooks 配置体系分为两类：

- `~/.openharness/settings.json`（全局配置）：这里配置的是“全局插件/钩子”，决定**哪些插件在所有 agent/tool/skill/事件上生效**，如统一的权限、审计、日志等切面。
- `<插件目录>/hooks/hooks.json`（插件级配置）：这里配置的是**插件自身的 hooks 及 matcher**，决定**该插件的钩子在具体哪些 tool/skill/agent/事件上生效**，如只对某类能力、某些事件插入逻辑。

这种设计模式下，**控制权在插件侧**，即插件声明“我在哪些能力/事件上插入逻辑”，而不是能力声明“我允许哪些插件扩展我”。

简明对比如下：

| 配置文件                      | 作用对象                  | 控制内容                                               |
|-------------------------------|---------------------------|--------------------------------------------------------|
| ~/.openharness/settings.json   | 全局（所有插件/能力）     | 配置全局 hooks/permissions/sandbox 等，影响所有能力     |
| <插件目录>/hooks/hooks.json   | 单个插件                  | 配置本插件的 hooks 及 matcher，决定在哪些能力/事件生效  |

> ⚠️ 不是“tool/skill/agent 配置允许哪些插件/钩子”，而是“插件声明自己在哪些能力/事件上生效”。

---

### 插件 hooks.json 及 matcher 精细控制

- 插件目录（如 plugins/my_plugin/）下的 hooks/hooks.json 文件，是该插件注册 hook（钩子）的入口。
- hooks.json 支持 matcher 字段，可以指定 hook 只对特定的 tool、skill、agent 或事件生效。例如 matcher: "my_skill_*" 只作用于以 my_skill_ 开头的能力。
- 通过 matcher 或更细粒度的配置，可以实现 hook 只在某些 skill/tool/agent 上生效，而不是所有能力。
- 这种机制让插件既能批量分发 hook，又能通过 matcher 精细控制 hook 的作用范围，实现灵活的扩展和安全隔离。

### 配置权归属与作用方向

- 插件 hooks.json 由**插件作者（即插件的使用者/程序员）**负责维护和声明。
- 插件作者决定 hook 的作用范围、事件类型、匹配对象等，能力本身无需声明允许哪些插件。
- 这种“插件自声明”机制，确保了插件的灵活性和可控性，避免了能力与插件的强耦合。

---
## 4. OpenHarness 支持的分层与配置维度一览

根据 OpenHarness 源码和配置体系，支持的所有分层与配置维度如下：

| 支持维度             | 配置文件（绝对路径）                                   | 配置示例说明                                                                 | 备注                                                         |
|----------------------|------------------------------------------------------|------------------------------------------------------------------------------|--------------------------------------------------------------|
| 全局 hook            | ~/.openharness/settings.json                          | "hooks": { "pre_tool_use": [ { "type": "command", ... } ] }                  | 全局生效，所有 agent/tool 调用前后均可触发                    |
| 插件级 hook          | <插件目录>/hooks/hooks.json                           | { "pre_tool_use": [ { "type": "prompt", ... } ] }                            | 仅该插件启用时生效                                           |
| 事件类型             | 同上                                                  | "hooks": { "session_start": [...], "post_tool_use": [...] }                  | 支持 session/tool use 等多种事件                             |
| hook 类型            | 同上                                                  | { "type": "command"/"prompt"/"http"/"agent", ... }                           | 支持多种 hook 类型，灵活扩展                                 |
| 权限模式             | ~/.openharness/settings.json                          | "permissions": { "mode": "strict" }                                          | default/strict/relaxed 等多种模式                            |
| 工具白名单/黑名单    | ~/.openharness/settings.json                          | "permissions": { "allowed_tools": ["Read"], "denied_tools": ["Shell"] }      | 控制哪些工具可用/禁用                                        |
| 路径规则             | ~/.openharness/settings.json                          | "permissions": { "path_rules": [ { "pattern": "/tmp/*", "allow": false } ] } | 支持 glob 匹配，细粒度控制文件操作权限                        |
| 命令规则             | ~/.openharness/settings.json                          | "permissions": { "denied_commands": ["rm -rf /"] }                           | 限制危险命令                                                 |
| 沙箱网络/文件系统    | ~/.openharness/settings.json                          | "sandbox": { "network": { ... }, "filesystem": { ... } }                     | 控制 agent 的网络/文件访问                                   |
| provider/workflow    | ~/.openharness/settings.json                          | "providers": { ... }                                                         | 支持多 LLM provider 配置与切换                               |
| 记忆/上下文相关      | ~/.openharness/settings.json                          | "memory": { ... }                                                            | 控制持久化记忆、上下文压缩等                                 |
| MCP/多智能体         | ~/.openharness/settings.json                          | "mcp": { ... }                                                               | MCP 协议与多 agent 协作                                      |

如需某一维度的详细说明或配置样例，请补充说明。
### hook 与 plugin 的本质关系与最佳理解方式

- **hook（钩子）** 是框架预定义的“插座”，在能力调用生命周期的关键节点（如 pre_tool_use、post_tool_use、session_start 等）暴露回调点，允许插入自定义逻辑。
- **plugin（插件）** 是“插头”，负责实现具体的 hook 逻辑。插件可以批量注册多个 hook，也可以注册 tool、skill、agent 等能力。
- hook 回调时会传递丰富的上下文（如当前 tool、输入参数、用户、环境等），plugin 可以根据上下文和全局/本地配置灵活决定是否执行、如何执行具体逻辑。
- 这种设计实现了“框架预埋插座 + 插件灵活插拔 + 上下文驱动决策”，极大提升了系统的可扩展性和可插拔性。

#### 正确理解

- hook 是扩展点（插座），plugin 是扩展实现（插头），上下文和配置决定了“插头”是否以及如何响应“插座”的调用。
- 切面（AOP）类比在 OpenHarness 中并非严格基于 tool 或 plugin，而是基于“事件驱动+能力注册”体系下的横切关注点实现。hook 是切面的载体，plugin 是切面的批量分发者，tool/skill/agent 是被切面的对象。
- 插件让切面批量化、可组合、可复用，但切面本身的生效范围和粒度是可配置和可编排的。

#### 最佳实践建议

- 设计切面时，优先考虑事件（如 pre_tool_use、post_tool_use、session_start 等）和能力类型（tool/skill/agent）。
- 用插件批量分发 hook，但用 matcher 或配置精细控制 hook 的作用范围。
- 保持 hook 逻辑解耦、可插拔，避免单一插件/能力耦合过重。

### 总结

- harness = tool 的“执行环境”+“前后处理”+“本地流程编排”
- permissions = 特殊的 hook，专注于权限控制
- hook = 插拔式扩展点，贯穿 harness、agent、tool 调用全流程

三者共同构建了安全、可控、可扩展的 AI 能力调用体系，其思想与 AOP 十分契合。
# subagent、skill、tool 的本质与关系

## 权威定义

- **tool**：能力的最小实现单元，通常绑定具体实现（如本地 API、脚本、插件等），协议为私有协议，参数和调用方式由实现方决定。
- **skill**：基于 MCP（Model Context Protocol）协议的能力描述，强调标准化、跨平台和可组合性，便于不同系统间能力复用和编排。
- **subagent**：对 tool/skill 的进一步组织和分层，相当于“能力代理”或“能力调度者”，根据任务类型、领域、上下文等对底层 tool/skill 进行分门别类和智能调度。

## 关系与作用

1. **tool 与 skill 的关系**
   - 本质都是“能力”的抽象和封装。
   - tool 偏向本地/私有实现，skill 偏向标准化和跨平台。
   - skill 可以包装 tool，提供统一协议和更强的组合能力。

2. **subagent 的意义**
   - 没有 subagent 时，LLM 需要在所有 tool/skill 里盲目检索，效率低且容易出错。
   - subagent 像“目录”一样分层管理能力，提升推理和调用的准确性。
   - subagent 负责将 tool/skill 按领域、任务、上下文等分门别类，便于 LLM 智能分析和调用。

3. **三者协同提升智能化水平**
   - tool/skill 提供底层能力，subagent 负责智能编排和调度。
   - 共同提升 LLM 的可用性、扩展性和智能化水平。

## 总结

- skill 和 tool 的本质都是能力的不同协议封装，subagent 是对能力的智能编排和分层。
- subagent、skill、tool 三者共同构建了高效、可扩展、智能化的 AI 能力调用体系。

---

> 例子：
> - 没有 subagent 时，LLM 相当于“大海捞针”；有了 subagent，相当于有了“目录”和“分类”，大大提升了检索和调用效率。
> - skill 是标准协议能力，tool 是本地实现能力，subagent 是能力的智能调度者。


Read [](file:///Users/zhanglizhi/workspace/sparrow/OpenHarness/src/openharness/config/settings.py#61-61), lines 61 to 180

根据 OpenHarness 源码和配置体系，支持的所有分层与配置维度如下，已补充到表格：

---

| 支持维度             | 配置文件（绝对路径）                                   | 配置示例说明                                                                 | 备注                                                         |
|----------------------|------------------------------------------------------|------------------------------------------------------------------------------|--------------------------------------------------------------|
| 全局 hook            | ~/.openharness/settings.json                          | "hooks": { "pre_tool_use": [ { "type": "command", ... } ] }                  | 全局生效，所有 agent/tool 调用前后均可触发                    |
| 插件级 hook          | <插件目录>/hooks/hooks.json                           | { "pre_tool_use": [ { "type": "prompt", ... } ] }                            | 仅该插件启用时生效                                           |
| 事件类型             | 同上                                                  | "hooks": { "session_start": [...], "post_tool_use": [...] }                  | 支持 session/tool use 等多种事件                             |
| hook 类型            | 同上                                                  | { "type": "command"/"prompt"/"http"/"agent", ... }                           | 支持多种 hook 类型，灵活扩展                                 |
| 权限模式             | ~/.openharness/settings.json                          | "permissions": { "mode": "strict" }                                          | default/strict/relaxed 等多种模式                            |
| 工具白名单/黑名单    | ~/.openharness/settings.json                          | "permissions": { "allowed_tools": ["Read"], "denied_tools": ["Shell"] }      | 控制哪些工具可用/禁用                                        |
| 路径规则             | ~/.openharness/settings.json                          | "permissions": { "path_rules": [ { "pattern": "/tmp/*", "allow": false } ] } | 支持 glob 匹配，细粒度控制文件操作权限                        |
| 命令规则             | ~/.openharness/settings.json                          | "permissions": { "denied_commands": ["rm -rf /"] }                           | 限制危险命令                                                 |
| 沙箱网络/文件系统    | ~/.openharness/settings.json                          | "sandbox": { "network": { ... }, "filesystem": { ... } }                     | 控制 agent 的网络/文件访问                                   |
| provider/workflow    | ~/.openharness/settings.json                          | "providers": { ... }                                                         | 支持多 LLM provider 配置与切换                               |
| 记忆/上下文相关      | ~/.openharness/settings.json                          | "memory": { ... }                                                            | 控制持久化记忆、上下文压缩等                                 |
| MCP/多智能体         | ~/.openharness/settings.json                          | "mcp": { ... }                                                               | MCP 协议与多 agent 协作                                      |

---

如需某一维度的详细说明或配置样例，请补充说明。