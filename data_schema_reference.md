# 数据 Schema 参考

资料核对日期：2026-05-21。本页定义课程推荐的数据字段。真实项目可以增删字段，但必须保留 model-visible 和 verifier-only 的边界。

## 1. Raw Log Schema

Raw log 是审计层，尽量原样记录执行过程。

| 字段 | 类型 | 必填 | 可见性 | 说明 |
|---|---|---:|---|---|
| `run_id` | string | 是 | metadata | 一次 agent 运行 ID |
| `task_id` | string | 是 | metadata | 任务 ID |
| `step_index` | integer | 是 | metadata | 第几步 |
| `timestamp` | string | 是 | metadata | ISO 时间 |
| `model_checkpoint` | string | 是 | metadata | 生成该步的模型 |
| `environment_version` | string | 是 | metadata | 环境快照或版本 |
| `assistant_output_raw` | string | 是 | model-visible-source | 模型原始输出 |
| `parsed_action` | object/null | 是 | model-visible-source | 解析出的 action |
| `tool_result_raw` | string/null | 是 | model-visible-source | 工具原始返回 |
| `tool_error` | string/null | 是 | model-visible-source | 工具错误 |
| `token_usage` | object | 否 | metadata | token 和成本 |

## 2. Trajectory Schema

Trajectory 是训练和评估中间层。

| 字段 | 类型 | 必填 | 可见性 | 说明 |
|---|---|---:|---|---|
| `task_id` | string | 是 | metadata | 任务 ID |
| `task` | string | 是 | model-visible | 用户任务 |
| `system` | string | 否 | model-visible | 系统指令 |
| `tools` | array | 是 | model-visible | 可用工具 |
| `steps` | array | 是 | mixed | 多步交互 |
| `final` | string | 是 | model-visible | 最终回答 |
| `final_status` | string | 是 | metadata | success/failure/partial |
| `failure_type` | string/null | 否 | metadata | 失败分类 |
| `verifier` | object | 是 | verifier-only | 验证结果 |
| `metadata` | object | 否 | metadata | 模型、环境、成本等 |

Step 字段：

| 字段 | 类型 | 必填 | 可见性 | 说明 |
|---|---|---:|---|---|
| `observation` | string/object | 是 | model-visible | 当前模型可见状态 |
| `action` | object | 是 | model-visible | 工具名和参数 |
| `result` | string/object | 是 | model-visible | 工具返回 |
| `error` | string/null | 是 | model-visible | 错误信息 |
| `provenance` | object | 否 | metadata | 来源、可信度、时间 |

## 3. SFT Sample Schema

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `messages` | array | 是 | role/content 消息 |
| `sample_id` | string | 否 | 样本 ID |
| `source_task_id` | string | 否 | 原任务 |
| `quality_grade` | string | 否 | A/B/C/reject |

Message：

| role | 是否算 loss | 说明 |
|---|---:|---|
| `system` | 否 | 稳定规则 |
| `user` | 否 | 用户任务 |
| `assistant` | 是 | action 或 final |
| `tool` | 否 | 环境返回 |

## 4. DPO Sample Schema

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `prompt` | string/array | 是 | 任务或消息前缀 |
| `chosen` | string/array | 是 | 更好回答或轨迹 |
| `rejected` | string/array | 是 | 更差回答或轨迹 |
| `chosen_reward` | number | 否 | chosen 分数 |
| `rejected_reward` | number | 否 | rejected 分数 |
| `preference_source` | string | 是 | verifier/human/judge/rule |
| `preference_reason` | string | 否 | 偏好理由 |
| `source_task_id` | string | 是 | 原任务 |

## 5. RL Prompt Schema

| 字段 | 类型 | 必填 | 可见性 | 说明 |
|---|---|---:|---|---|
| `task_id` | string | 是 | metadata | 任务 ID |
| `prompt` | string | 是 | model-visible | 任务输入 |
| `environment` | string/object | 是 | verifier-only | 环境 ID 或配置 |
| `tools` | array | 是 | model-visible | 可用工具 |
| `max_steps` | integer | 是 | model-visible | 最大步数 |
| `verifier` | string/object | 是 | verifier-only | 验证器配置 |
| `safety_policy` | string/object | 否 | model-visible | 安全约束 |

## 6. Dataset Card Schema

| 字段 | 必填 | 说明 |
|---|---:|---|
| `dataset_name` | 是 | 数据集名 |
| `version` | 是 | 版本 |
| `created_at` | 是 | 创建时间 |
| `source_runs` | 是 | 来源 run |
| `task_types` | 是 | 任务类型 |
| `num_tasks` | 是 | 任务数 |
| `num_samples` | 是 | 样本数 |
| `split_method` | 是 | split 方法 |
| `quality_filters` | 是 | 过滤规则 |
| `redaction_policy` | 是 | 隐私清洗 |
| `known_limitations` | 是 | 已知限制 |

