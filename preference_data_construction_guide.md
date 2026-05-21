# Preference / DPO 数据构造手册

资料核对日期：2026-05-21。参考 RLHF Book 的 Preference Data、Hugging Face Alignment Handbook 的 DPO 数据格式、UltraFeedback/Orca DPO pairs、Towards Comprehensive Preference Data Collection for Reward Modeling，以及 data-centric RLHF 相关研究。

## 1. Preference 数据的目标

Preference 数据不是“正确答案数据”，而是行为比较数据：

```text
在同一个 prompt 下，chosen 比 rejected 更好
```

对 agent 来说，比较对象应该是整条轨迹：

```text
prompt + trajectory_chosen > prompt + trajectory_rejected
```

## 2. 标准 DPO 格式

简单格式：

```json
{
  "prompt": "修复 parser 空输入 bug。",
  "chosen": "Action: run_tests...\nAction: read_file...\nAction: edit_file...\nAction: run_tests...\nFinal: 通过测试。",
  "rejected": "Final: 可能是 parser.py 的问题。"
}
```

Conversational 格式：

```json
{
  "chosen": [
    {"role": "user", "content": "修复 parser 空输入 bug。"},
    {"role": "assistant", "content": "Action: run_tests..."},
    {"role": "tool", "content": "FAILED"},
    {"role": "assistant", "content": "Final: 通过测试。"}
  ],
  "rejected": [
    {"role": "user", "content": "修复 parser 空输入 bug。"},
    {"role": "assistant", "content": "Final: 可能是 parser.py 的问题。"}
  ]
}
```

格式要和训练框架一致。Alignment Handbook 风格的数据常用 `chosen` / `rejected` 列，内容是 role/content 消息列表。

## 3. Pair 构造流程

推荐流程：

```text
prompt generation
-> response / trajectory generation
-> response filtering
-> verifier or human labeling
-> pair construction
-> pair audit
```

这和 preference data collection 研究里常见的四步框架一致：prompt、response、filtering、labeling。

## 4. Chosen / Rejected 来源

优先级：

1. verifier 成功 vs verifier 失败。
2. hidden tests 通过 vs visible tests 通过但 hidden 失败。
3. 人类明确偏好。
4. 多 judge 一致偏好。
5. 规则偏好，例如有验证 > 无验证。

不要只靠一个 LLM judge。

## 5. Hard Negative

好的 rejected 不是胡说八道，而是“很像对，但关键错”。

例子：

- 格式正确但工具选错。
- 修改了代码但没跑测试。
- 通过 visible tests 但 hidden tests 失败。
- 网页到达正确页面但提交了错误表单。
- API 调用成功但修改了错误用户。

Hard negative 能让 DPO 学到细粒度偏好。

## 6. Pair Gap

建议记录：

```text
chosen_reward
rejected_reward
reward_gap
```

起步可以只用：

```text
reward_gap >= 0.5
```

或：

```text
chosen = success, rejected = failure
```

弱 pair 可以保留，但单独分桶，不要和强 pair 混在一起不加权训练。

## 7. 长度控制

如果 chosen 总是更长，DPO 会学到 length bias。

检查：

```text
chosen_avg_tokens
rejected_avg_tokens
chosen/rejected length ratio
```

处理：

- 构造“短但正确 > 长但错”pair。
- 控制同一 pair 的长度差。
- 训练报告记录 avg output length。

## 8. 截断检查

DPO pair 很容易超长。截断后可能变成：

```text
chosen 关键成功步骤被截断
rejected 失败步骤被截断
```

处理：

- 训练前模拟 tokenization。
- 统计 `truncated_pair_rate`。
- 抽查被截断样本。
- 对长 trajectory 先摘要再构造 pair。

## 9. Preference 数据审计

每批数据记录：

```text
num_pairs
num_prompts
pairs_per_prompt
chosen_avg_tokens
rejected_avg_tokens
reward_gap_avg
reward_gap_p10
truncated_pair_rate
judge_source_distribution
human_label_rate
verifier_label_rate
label_conflict_rate
```

抽查重点：

- reward gap 小的 pair。
- chosen/rejected 长度差极大的 pair。
- judge 和 verifier 冲突的 pair。
- LLM judge 高分但 verifier 失败的 pair。

