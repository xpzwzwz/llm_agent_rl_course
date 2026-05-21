# 第三课：Agent 数据和 Trajectory

## 1. Agent 数据的基本单位

Agent 训练最重要的数据单位不是单条问答，而是一条 trajectory。

一条 trajectory 记录一次完整任务：

```json
{
  "task": "修复项目里的 failing test。",
  "trajectory": [
    {
      "observation": "pytest 显示 test_parser.py::test_empty_input 失败。",
      "action": {
        "name": "read_file",
        "arguments": {"path": "src/parser.py"}
      },
      "result": "文件内容..."
    },
    {
      "observation": "parse_empty 没有处理空字符串。",
      "action": {
        "name": "edit_file",
        "arguments": {"path": "src/parser.py", "patch": "..."}
      },
      "result": "编辑成功。"
    },
    {
      "action": {
        "name": "run_tests",
        "arguments": {"command": "pytest tests/test_parser.py -q"}
      },
      "result": "3 passed"
    }
  ],
  "final_status": "success",
  "final_reward": 1.0
}
```

## 2. 字段怎么设计

建议最少保留这些字段：

- `task`：原始用户任务。
- `observation`：当前可见环境状态。
- `action`：工具名和参数。
- `result`：工具执行结果。
- `final`：最终回答或提交说明。
- `final_status`：success、failure、partial。
- `reward`：可选，过程奖励。
- `metadata`：模型名、温度、时间、环境版本。

如果要做 DPO，还要记录对比样本：

```json
{
  "task": "...",
  "chosen_trajectory": "...",
  "rejected_trajectory": "...",
  "preference_reason": "chosen 运行了测试并修复失败，rejected 没有验证结果。"
}
```

## 3. 成功样本和失败样本都重要

只收成功样本会导致模型学不到恢复策略。失败样本也有价值，尤其是这些类型：

- 工具调用失败后成功恢复。
- 搜索结果不可靠后换信息源。
- 测试失败后定位错误。
- 参数错误后修正参数。
- 发现任务不可完成后明确说明限制。

但失败样本不能无脑喂给 SFT。否则模型会模仿失败行为。更好的用法是：

- 把失败后成功恢复的轨迹放进 SFT。
- 把失败轨迹作为 DPO 的 rejected。
- 把失败原因用于 reward shaping。

## 4. 数据清洗

Agent 数据容易很脏。清洗时重点看：

- 是否包含隐私信息、token、cookie、内部 URL。
- 工具返回值是否过长，是否需要摘要。
- action 是否真的执行过，而不是模型编造。
- final_status 是否可信。
- 成功是否经过自动验证。
- 同一任务是否有重复轨迹。

对 GitHub 和网页数据尤其要注意许可证、隐私和服务条款。

## 5. 最小数据集建议

如果只是验证训练流程，可以先做一个小数据集：

- 200 条工具调用任务。
- 100 条网页信息查找任务。
- 100 条小型代码修复任务。
- 每条任务至少 1 条成功轨迹。
- 每条任务尽量配 1 条失败或低质量轨迹。

这个规模不能训练出强 agent，但足够验证数据格式、SFT、DPO、评估脚本和错误分析流程。

