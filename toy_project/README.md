# Agent RL Toy Project

这个目录是课程的最小可运行项目。它不训练真实大模型，而是跑通 agent 训练数据闭环：

```text
tasks -> collect trajectories -> verify -> build SFT dataset -> build DPO dataset -> eval report
```

## 文件

- `data/tasks.jsonl`：小型任务集。
- `env/corpus/*.md`：agent 可搜索和读取的文档语料。
- `tools.py`：受控工具函数。
- `verifier.py`：简单自动验证器。
- `collect_trajectories.py`：采集 toy trajectories。
- `build_sft_dataset.py`：从成功轨迹生成 SFT JSONL。
- `build_dpo_dataset.py`：从成功/失败轨迹生成 DPO JSONL。
- `make_eval_report.py`：生成评估报告。
- `tests/`：单元测试。

## 运行

在 `/home/xp/playground` 下运行：

```bash
python docs/llm_agent_rl_course/toy_project/collect_trajectories.py
python docs/llm_agent_rl_course/toy_project/build_sft_dataset.py
python docs/llm_agent_rl_course/toy_project/build_dpo_dataset.py
python docs/llm_agent_rl_course/toy_project/make_eval_report.py
python -m pytest docs/llm_agent_rl_course/toy_project/tests -q
```

输出文件会写到 `docs/llm_agent_rl_course/toy_project/data/` 和 `reports/`。

