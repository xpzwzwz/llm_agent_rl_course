# 第五课：GitHub 和代码 Agent

## 1. 代码 Agent 的任务形态

代码 agent 通常面对这样的任务：

```text
这个仓库有一个 issue：安装后运行 pytest 失败。请定位原因并修复。
```

它需要完成：

- 阅读 issue 和复现步骤。
- 浏览项目结构。
- 搜索相关代码。
- 运行测试。
- 修改文件。
- 再次运行测试。
- 总结修复。

这比普通代码补全更接近真实软件工程。

## 2. SWE-bench 的意义

SWE-bench 使用真实 GitHub issue 和对应仓库，评估模型能否生成可通过测试的 patch。它对 coding agent 很重要，因为最终结果可以自动验证：

```text
patch applied + tests pass -> 成功
```

这比让 LLM judge 判断“回答是否合理”更可靠。

## 3. OpenHands 的工程启发

OpenHands 是一个面向软件工程任务的 agent 项目。根据 2026-05-21 的 GitHub API 查询，`OpenHands/OpenHands` 约有 74,329 stars，最近 push 在 2026-05-21。

它代表的训练/评估思路是：

```text
LLM -> shell/read/edit/test 工具 -> 仓库环境 -> patch -> 验证
```

如果你想训练 coding agent，可以从这类系统中采集轨迹：

- 读了哪些文件。
- 用了哪些搜索命令。
- 运行了哪些测试。
- 修改了哪些 patch。
- 哪些测试先失败后通过。
- 最终是否解决 issue。

## 4. GitHub 数据怎么用

GitHub 数据常见来源：

- issue 描述。
- pull request 讨论。
- commit diff。
- CI 日志。
- 测试文件。
- release note。

但要注意：直接用 PR diff 做训练，模型可能只学到“答案”，学不到排查过程。更好的数据是 agent 真实执行轨迹：

```text
issue -> reproduce -> inspect -> edit -> test -> final
```

如果没有真实轨迹，可以用 issue + patch 构造弱监督数据，但要标明它不是完整 agent 轨迹。

## 5. Coding Agent 的 Reward

代码任务 reward 可以很明确：

- 单元测试通过。
- 新增测试覆盖了 bug。
- lint/type check 通过。
- patch 尽量小。
- 没有修改无关文件。
- 没有删除测试或绕过断言。

危险的 reward 是：

```text
只要测试通过就满分。
```

模型可能学会删除测试、改配置跳过测试、硬编码答案。训练环境必须保护测试文件，或者在隐藏测试上验证。

