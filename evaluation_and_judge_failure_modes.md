# 评估和 LLM Judge 问题清单

资料核对日期：2026-05-21。参考 RLHF Book、Hugging Face Alignment Handbook、Braintrust/Weights & Biases 关于 LLM-as-a-judge 的讨论、FlowVerify 对 judge failure modes 的总结，以及 preference leakage、length bias、reward overoptimization 相关研究。

这份文档专门讲评估问题。评估错了，训练会朝错误方向优化。

## 1. Position Bias

LLM judge 在 pairwise 比较时可能偏好 A 位置或 B 位置，而不是偏好真实更好的回答。

坏评估：

```text
Judge: A 比 B 好
```

但换顺序后：

```text
Judge: B 比 A 好
```

处理：

- 同一 pair 评两次，交换顺序。
- 只在两次一致时采纳。
- 记录 `position_flip_rate`。
- 对接近质量的 pair 更谨慎。

## 2. Verbosity / Length Bias

Judge 常偏好更长、更像报告的回答，即使短回答更准确。

表现：

- DPO chosen 普遍比 rejected 长很多。
- 训练后模型越来越啰嗦。
- reward 上升但 cost 和 avg_tokens 暴涨。

处理：

- 单独记录长度。
- judge rubric 明确“不要因长度加分”。
- 构造“短但正确 > 长但错”的 pair。
- 加 cost metric，不只看 judge score。

## 3. Format Bias

Judge 可能偏好 markdown、项目符号、标题结构，而不是内容质量。

风险：

- 模型学会“格式漂亮”。
- 真实任务正确率不升。
- DPO 后回答变模板化。

处理：

- 内容分和格式分分开。
- 对相同内容不同格式做 sanity check。
- 不把格式分直接等同任务成功。

## 4. Self-Preference / Nepotism Bias

同一模型家族的 judge 可能偏好同一模型家族生成的文本。

处理：

- judge 和 candidate 使用不同模型家族。
- 多 judge 投票。
- 加人类锚点样本。
- 记录 judge/provider 版本。

## 5. Calibration Drift

同一个 judge 在不同时间、不同版本、不同系统提示下，评分尺度可能漂移。

处理：

- 固定 judge model version。
- 固定 judge prompt。
- 保留 anchor set。
- 每次评估先跑 anchor set，看分布是否变了。

## 6. Preference Leakage

如果 synthetic data generator、judge、训练模型高度相关，偏好数据可能泄漏风格而不是质量。模型会学会迎合 judge，而不是学会任务。

处理：

- generator 和 judge 分离。
- verifier 优先于 judge。
- 对 judge-friendly 样本人工抽查。
- 训练和评估使用不同 judge 或不同判据。

## 7. LLM Judge 不是 Verifier

LLM judge 可以判断风格、完整性、相关性，但它不是可靠的事实验证层。

优先级应该是：

```text
deterministic verifier > hidden tests > structured assertions > LLM judge > 纯人工印象
```

适合 LLM judge 的场景：

- 开放式回答质量。
- 摘要完整性。
- 风格和语气。
- 低风险初筛。

不适合单独依赖 LLM judge 的场景：

- 代码 patch 正确性。
- 金融/医疗/法律高风险判断。
- agent 是否执行了真实工具。
- 数据是否泄露。

## 8. Eval Set Contamination

评估任务可能出现在训练语料、GitHub issue、benchmark 讨论或模型预训练数据中。

处理：

- 使用私有 held-out 任务。
- 定期换 eval set。
- 对公开 benchmark 分数保持怀疑。
- 保存任务创建时间和来源。

## 9. Metric Gaming

模型优化某个指标后，会牺牲未监控维度。

例子：

```text
只优化 success_rate -> 成本暴涨
只优化 avg_steps -> 提前结束
只优化 judge score -> 啰嗦模板化
只优化 visible tests -> hidden tests 下降
```

处理：

- 指标组合：success、cost、safety、hidden checks。
- 设 block metric：安全失败直接不通过。
- 高分样本抽查。

## 10. 评估报告必须包含

```text
model_checkpoint
eval_set_version
judge_model_version
verifier_version
success_rate
hidden_success_rate
avg_steps
avg_tokens
invalid_action_rate
premature_final_rate
judge_position_flip_rate
length_distribution
cost_per_success
top_failure_modes
```

没有这些字段，很难判断训练是否真的变好。

