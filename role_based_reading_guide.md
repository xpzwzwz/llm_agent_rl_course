# 按角色阅读路线

这份文档帮助团队成员快速找到自己该看的内容。

## 1. 数据工程师

目标：把 raw log 转成可训练、可审计的数据。

必读：

- [Agent Trajectory 数据构造手册](agent_trajectory_data_guide.md)
- [数据 Schema 参考](data_schema_reference.md)
- [数据质量 Rubric](data_quality_rubric.md)
- [数据版本变更模板](dataset_change_log_template.md)

重点掌握：

- model-visible 和 verifier-only 字段隔离。
- raw log 不要丢。
- task-level split。
- dataset card 和 change log。

## 2. 标注负责人

目标：组织人类偏好标注和质量复审。

必读：

- [标注员操作指南](annotation_guideline.md)
- [Preference / DPO 数据构造手册](preference_data_construction_guide.md)
- [Reward Model 数据构造手册](reward_model_data_guide.md)
- [坏数据案例库](bad_data_examples.md)

重点掌握：

- chosen/rejected 的判断优先级。
- hard negative。
- 标注冲突处理。
- gold questions 和复审机制。

## 3. 训练工程师

目标：把数据用于 SFT/DPO/GRPO/PPO，并定位训练问题。

必读：

- [训练配方：SFT、DPO、PPO、GRPO 怎么落地](training_recipes.md)
- [多阶段 Post-Training 数据策略](multi_stage_data_strategy.md)
- [数据混比和 Curriculum 设计](data_mixture_and_curriculum.md)
- [训练过程问题清单](training_process_failure_modes.md)

重点掌握：

- 每阶段用什么数据。
- 数据混比和遗忘。
- DPO 后变短、不行动。
- GRPO reward std 和 reward hacking。

## 4. 评估负责人

目标：证明模型真的变强，而不是指标被刷高。

必读：

- [评估和 LLM Judge 问题清单](evaluation_and_judge_failure_modes.md)
- [第七课：评估基准和自建 Benchmark](lesson_07_evaluation_benchmarks.md)
- [数据问题排查索引](data_debugging_index.md)

重点掌握：

- held-out eval。
- LLM judge 偏差。
- hidden checks。
- 分场景评估。

## 5. 安全审核

目标：防止训练数据和 agent 行为引入安全风险。

必读：

- [Agent 安全和工具边界问题清单](agent_security_and_tool_failure_modes.md)
- [第十一课：Sandbox 和环境设计](lesson_11_sandbox_and_environment_design.md)
- [第十二课：Reward Hacking 和训练排错](lesson_12_reward_hacking_and_debugging.md)

重点掌握：

- prompt injection。
- secret leakage。
- verifier tampering。
- unsafe action 负样本回流。

## 6. 项目负责人

目标：决定优先级和里程碑。

必读：

- [数据问题严重级别](data_issue_severity_levels.md)
- [多阶段 Post-Training 数据策略](multi_stage_data_strategy.md)
- [生产数据回流流程](production_data_feedback_loop.md)
- [数据版本变更模板](dataset_change_log_template.md)

重点掌握：

- 什么是 blocker。
- 一周能做什么。
- 一个月能做什么。
- 数据变更如何验收和回滚。

