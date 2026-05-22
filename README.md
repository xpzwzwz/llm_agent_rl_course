# 大模型 Agent 强化学习零基础课程

这组文档面向想训练或改进 LLM agent 的学习者。目标不是只列论文，而是让你能理解：agent 能力是什么、训练数据长什么样、SFT/DPO/GRPO/PPO 各自解决什么问题、数据构造如何跨多阶段演化，以及如何搭一个最小可行训练闭环。

资料核对日期：2026-05-21。主要依据 ToolBench、WebArena、SWE-bench、AgentGym、DeepSeek-R1、DPO、RLHF/RLAIF 相关论文，以及 TRL、OpenRLHF、verl、LLaMA-Factory、ms-swift、LangGraph、AutoGen、OpenHands、browser-use 等公开资料。

## 按目的查找

我想先入门：

- [第一课：LLM Agent 是什么](lesson_01_what_is_agent.md)
- [第二课：工具调用和 Function Calling](lesson_02_tool_use_and_function_calling.md)
- [第三课：Agent 数据和 Trajectory](lesson_03_agent_data_and_trajectories.md)

我想训练模型：

- [第六课：用 SFT、DPO 和 RL 训练 Agent](lesson_06_sft_dpo_rl_for_agents.md)
- [训练配方：SFT、DPO、PPO、GRPO 怎么落地](training_recipes.md)
- [第十四课：Agent RLHF 的技术原理](lesson_14_rlhf_math_for_agents.md)

我想构造数据：

- [数据构造问题清单](data_construction_failure_modes.md)
- [数据构造工作流总览](data_workflow_overview.md)
- [多阶段 Post-Training 数据策略](multi_stage_data_strategy.md)
- [数据混比和 Curriculum 设计](data_mixture_and_curriculum.md)

我遇到数据问题：

- [数据问题排查索引](data_debugging_index.md)
- [数据决策树](data_decision_trees.md)
- [数据构造 FAQ](data_construction_faq.md)
- [数据问题严重级别](data_issue_severity_levels.md)

我要做团队落地：

- [按角色阅读路线](role_based_reading_guide.md)
- [标注员操作指南](annotation_guideline.md)
- [生产数据回流流程](production_data_feedback_loop.md)
- [数据版本变更模板](dataset_change_log_template.md)

## 快速开始

- [第十三课：端到端 Toy Project](lesson_13_end_to_end_toy_project.md)
- [toy_project/README.md](toy_project/README.md)
- [real_training_lab/README.md](real_training_lab/README.md)
- [开源项目学习路线](open_source_study_guide.md)
- [原理学习项目推荐](principle_learning_projects.md)

课程目录里包含一个最小可运行项目：

```text
docs/llm_agent_rl_course/toy_project
```

它演示从任务集采集轨迹、自动验证、生成 SFT/DPO 数据和输出评估报告的完整闭环。

## 基础概念

- [第一课：LLM Agent 是什么](lesson_01_what_is_agent.md)
- [第二课：工具调用和 Function Calling](lesson_02_tool_use_and_function_calling.md)
- [第三课：Agent 数据和 Trajectory](lesson_03_agent_data_and_trajectories.md)
- [第四课：网页和浏览器 Agent](lesson_04_web_and_browser_agents.md)
- [第五课：GitHub 和代码 Agent](lesson_05_github_coding_agents.md)
- [第十课：工具调用格式怎么选](lesson_10_tool_calling_formats.md)
- [第十一课：Sandbox 和环境设计](lesson_11_sandbox_and_environment_design.md)

## 训练方法和原理

- [第六课：用 SFT、DPO 和 RL 训练 Agent](lesson_06_sft_dpo_rl_for_agents.md)
- [训练配方：SFT、DPO、PPO、GRPO 怎么落地](training_recipes.md)
- [第十四课：Agent RLHF 的技术原理](lesson_14_rlhf_math_for_agents.md)
- [第十五课：长程 Agent 的 Credit Assignment](lesson_15_credit_assignment_and_long_horizon_agents.md)
- [开源项目学习路线](open_source_study_guide.md)
- [原理学习项目推荐](principle_learning_projects.md)

## 数据构造

- [第九课：Agent 训练数据管线](lesson_09_agent_training_data_pipeline.md)
- [数据构造问题清单](data_construction_failure_modes.md)
- [SFT 数据构造手册](sft_data_construction_guide.md)
- [Preference / DPO 数据构造手册](preference_data_construction_guide.md)
- [Reward Model 数据构造手册](reward_model_data_guide.md)
- [Agent Trajectory 数据构造手册](agent_trajectory_data_guide.md)
- [数据 Schema 参考](data_schema_reference.md)
- [数据质量 Rubric](data_quality_rubric.md)
- [坏数据案例库](bad_data_examples.md)
- [多阶段 Post-Training 数据策略](multi_stage_data_strategy.md)
- [数据混比和 Curriculum 设计](data_mixture_and_curriculum.md)

## 数据排查和团队流程

- [数据问题排查索引](data_debugging_index.md)
- [数据决策树](data_decision_trees.md)
- [数据构造 FAQ](data_construction_faq.md)
- [数据问题案例](data_case_studies.md)
- [数据 Before / After 示例](data_before_after_examples.md)
- [数据失败复盘模板](data_failure_postmortem_template.md)
- [数据版本变更模板](dataset_change_log_template.md)
- [按角色阅读路线](role_based_reading_guide.md)
- [标注员操作指南](annotation_guideline.md)
- [生产数据回流流程](production_data_feedback_loop.md)
- [业务域数据构造配方](domain_specific_data_recipes.md)
- [数据问题严重级别](data_issue_severity_levels.md)

## 高级数据专题

- [数据许可和治理 FAQ](legal_and_data_governance_faq.md)
- [多模态 / VLM Agent 数据 FAQ](multimodal_agent_data_faq.md)
- [RAG / Search Agent 数据 FAQ](rag_search_agent_data_faq.md)
- [长上下文数据 FAQ](long_context_data_faq.md)
- [采样和成本策略](sampling_and_cost_strategy.md)
- [Benchmark 去污染](benchmark_decontamination.md)
- [公开数据集导读](public_dataset_reading_guide.md)

## 评估、安全和排错

- [第七课：评估基准和自建 Benchmark](lesson_07_evaluation_benchmarks.md)
- [第八课：搭建你自己的 Agent 训练闭环](lesson_08_build_your_own_training_loop.md)
- [第十二课：Reward Hacking 和训练排错](lesson_12_reward_hacking_and_debugging.md)
- [训练过程问题清单](training_process_failure_modes.md)
- [评估和 LLM Judge 问题清单](evaluation_and_judge_failure_modes.md)
- [Agent 安全和工具边界问题清单](agent_security_and_tool_failure_modes.md)

## 参考资料

- [术语表](glossary.md)
- [资料链接](resources.md)

## 你应该先记住的主线

普通聊天模型的核心能力是：

```text
用户问题 -> 文本回答
```

Agent 模型的核心能力是：

```text
任务 -> 观察环境 -> 规划 -> 调用工具 -> 读取结果 -> 修正计划 -> 继续行动 -> 完成任务
```

所以训练 agent 时，不能只优化单轮回答。你要优化整条任务轨迹：工具选得对不对、参数填得准不准、是否根据结果调整计划、是否验证最终结果、是否能在失败时恢复。

## 推荐学习路线

如果你刚开始，不要一上来做在线 RL。优先顺序是：

1. 先理解 agent 的行为循环：observation、action、result、final。
2. 用 LangGraph、OpenHands、browser-use 这类框架跑出可记录的轨迹。
3. 收集成功轨迹和失败轨迹，先做 SFT。
4. 把好轨迹和坏轨迹配成 preference pair，再做 DPO。
5. 对有自动验证器的任务，例如代码测试、网页任务完成、API 返回检查，再考虑 GRPO/PPO。
6. 建立固定评估集，否则 reward 上升不等于 agent 真的变强。
