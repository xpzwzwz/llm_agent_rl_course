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
data/heldout_eval_tasks.jsonl
```

`eval_tasks.jsonl` 包含 toy train tasks 加 3 条 held-out smoke tasks。这个 eval 只用于验证训练闭环和格式行为，不代表泛化能力。

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

也可以使用配置文件：

```bash
python train_sft_lora.py --config configs/sft_lora.yaml
```

这个 toy 数据很小。预期是训练 loss 会下降，但 eval 未必显著提升。

## 4. SFT eval

```bash
python eval_agent.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --base_model Qwen/Qwen2.5-0.5B-Instruct \
  --adapter_path outputs/sft_lora
```

`outputs/sft_lora` 是 LoRA adapter，不是完整 merged model。评估 adapter 时必须同时提供 base model。

## 5. 可选 DPO

```bash
python train_dpo_lora.py \
  --model_name Qwen/Qwen2.5-0.5B-Instruct \
  --adapter_path outputs/sft_lora \
  --dataset_path data/train_dpo.jsonl \
  --output_dir outputs/dpo_lora
```

也可以使用配置文件：

```bash
python train_dpo_lora.py --config configs/dpo_lora.yaml
```

DPO 的学习重点是 preference pair 格式和 chosen/rejected 构造，不是追求 toy benchmark 分数。

## 常见报错

### assistant-only loss / chat template 报错

`train_sft_lora.py` 使用 `assistant_only_loss=True`。这依赖 TRL 版本、tokenizer chat template 和 messages 格式能产生 assistant mask。

如果报错：

- 升级 TRL。
- 打印一条样本的 chat template 渲染结果。
- 暂时改成 `assistant_only_loss=False` 跑通流程，再回头修 mask。

### SFT 后 eval 找不到模型

LoRA 训练默认保存 adapter。请用：

```bash
python eval_agent.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --base_model Qwen/Qwen2.5-0.5B-Instruct \
  --adapter_path outputs/sft_lora
```

不要直接把 adapter 目录当完整模型传给 `--model`。

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
