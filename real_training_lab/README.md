# Real Training Lab：最小真实训练实验

这个实验的目标不是训练出强 agent，而是让你真实跑通一轮：

```text
toy_project 轨迹数据
-> TRL 可训练格式
-> LoRA SFT
-> 固定 eval
-> 可选 DPO
-> 实验报告
```

推荐模型：

```text
Qwen/Qwen2.5-0.5B-Instruct
Qwen/Qwen2.5-1.5B-Instruct
```

如果在 Colab 或消费级 GPU 上运行，优先用 0.5B。

## 安装

```bash
cd /home/xp/playground/docs/llm_agent_rl_course/real_training_lab
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 1. 准备数据

```bash
python prepare_dataset.py
```

输出：

```text
data/train_sft.jsonl
data/train_dpo.jsonl
data/eval_tasks.jsonl
```

## 2. 跑 base eval

不下载模型的 smoke test：

```bash
python eval_agent.py --model rule
```

真实模型：

```bash
python eval_agent.py --model Qwen/Qwen2.5-0.5B-Instruct
```

## 3. LoRA SFT

```bash
python train_sft_lora.py \
  --model_name Qwen/Qwen2.5-0.5B-Instruct \
  --dataset_path data/train_sft.jsonl \
  --output_dir outputs/sft_lora
```

这个 toy 数据很小。预期是训练 loss 会下降，但 eval 未必显著提升。

## 4. SFT eval

```bash
python eval_agent.py --model outputs/sft_lora
```

## 5. 可选 DPO

```bash
python train_dpo_lora.py \
  --model_name Qwen/Qwen2.5-0.5B-Instruct \
  --adapter_path outputs/sft_lora \
  --dataset_path data/train_dpo.jsonl \
  --output_dir outputs/dpo_lora
```

DPO 的学习重点是 preference pair 格式和 chosen/rejected 构造，不是追求 toy benchmark 分数。

## 6. 写报告

复制并填写：

```text
reports/example_report.md
```

重点记录：

- base / SFT / DPO success rate。
- invalid action rate。
- premature final rate。
- 失败样例。
- 下一轮数据怎么改。

