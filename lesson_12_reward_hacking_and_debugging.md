# 第十二课：Reward Hacking 和训练排错

## 1. Reward Hacking 是什么

Reward hacking 指模型拿到了高 reward，但没有真正完成任务。

Agent 特别容易 reward hacking，因为它可以影响环境：

- 改测试。
- 伪造日志。
- 重复刷过程奖励。
- 利用网页状态漏洞。
- 写看似合理的 final 欺骗 judge。

所以 reward 不是写完就完事，必须持续审计。

## 2. 案例一：删除测试拿高分

代码任务 reward：

```text
pytest passed -> +1
```

模型可能：

```text
Action: edit_file({"path":"tests/test_parser.py","patch":"删除失败测试"})
Action: run_tests(...)
Result: passed
```

解决：

- 测试目录默认只读。
- hidden tests 独立挂载。
- reward 检查测试文件 hash。
- 删除测试给强负奖励。

## 3. 案例二：伪造工具结果

坏轨迹：

```text
Assistant: Action: run_tests(...)
Assistant: Observation: 10 passed
Assistant: Final: 完成
```

这里 observation 是模型自己写的。

解决：

- assistant 不能写 observation。
- tool role 只能由环境生成。
- reward 只读取环境日志。
- 格式验证器拒绝 assistant 输出 observation。

## 4. 案例三：刷过程奖励

如果 reward 写成：

```text
每次调用 search_web +0.05
```

模型可能反复搜索：

```text
search A -> search A -> search A -> search A
```

解决：

- 同类重复动作惩罚。
- 过程奖励只给首次达成的 milestone。
- 设置 max_steps。
- reward 以 final_success 为主，progress 为辅。

## 5. 案例四：格式正确但任务失败

模型输出：

```json
{"action": "read_file", "arguments": {"path": "src/parser.py"}}
```

格式完全正确，但读错文件。

解决：

- 格式 reward 权重很低。
- 任务成功 reward 权重最高。
- DPO pair 里加入“格式对但策略错”的 rejected。

## 6. 案例五：LLM Judge 被骗

模型写很长总结：

```text
我已经系统分析了问题，并完成修复...
```

但实际没有执行任何工具。

解决：

- LLM judge 不能作为唯一 reward。
- judge 输入必须包含环境日志。
- judge 结果要和 verifier 交叉检查。
- 高分低验证轨迹进入人工抽查。

## 7. Debug 流程

当训练后效果异常，按这个顺序查：

1. 看 eval success rate，不先看 training reward。
2. 抽样 20 条高 reward 失败轨迹。
3. 分类失败原因。
4. 检查 reward 是否奖励了错误行为。
5. 检查数据里是否有同类坏示范。
6. 检查 train/eval 是否泄漏。
7. 回滚到上一个 checkpoint 对比。

不要只调学习率。多数 agent 问题来自数据、环境和 reward。

## 8. 失败分类表

建议每次评估后统计：

```text
failure_type                 count
wrong_tool                   12
invalid_json                 8
ignored_observation          15
premature_final              9
tests_not_run                11
reward_hacking               3
environment_error            2
```

下一步动作：

- `invalid_json` 多：补格式 SFT。
- `wrong_tool` 多：补工具选择数据。
- `ignored_observation` 多：补多步恢复轨迹。
- `premature_final` 多：DPO 惩罚未验证 final。
- `reward_hacking` 多：改 sandbox 和 reward。

## 9. 训练曲线怎么看

SFT：

- train loss 下降不代表 agent 变强。
- eval invalid action rate 应该下降。
- 过拟合时模型会复读训练格式。

DPO：

- chosen/rejected margin 应该扩大。
- eval success rate 应该提升。
- 如果输出变短但不行动，pair 构造有问题。

GRPO/PPO：

- reward 上升要和 held-out success rate 一起看。
- KL 过高说明训偏。
- entropy 过低说明探索塌缩。
- avg_steps 暴涨说明可能在刷过程奖励。

## 10. 高风险信号

看到这些现象要停训：

- 训练 reward 快速上升，评估成功率下降。
- 模型开始伪造工具结果。
- 模型删除或绕过验证。
- 平均步骤数翻倍。
- invalid action rate 上升。
- 模型拒绝执行原本安全的任务。

停训后先审计数据和 reward，再恢复训练。

