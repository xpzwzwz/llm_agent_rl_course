# Real Training Lab 实验报告模板

## 环境

- GPU / CPU：
- CUDA：
- Python：
- model：
- LoRA config：
- dataset size：

## 运行命令

```bash
python prepare_dataset.py
python eval_agent.py --model rule
python train_sft_lora.py --model_name Qwen/Qwen2.5-0.5B-Instruct
python eval_agent.py --model Qwen/Qwen2.5-0.5B-Instruct --base_model Qwen/Qwen2.5-0.5B-Instruct --adapter_path outputs/sft_lora
```

## 结果

| model | success_rate | invalid_action_rate | avg_steps | premature_final_rate | parse_error_rate |
|---|---:|---:|---:|---:|---:|
| base |  |  |  |  |  |
| sft |  |  |  |  |  |
| dpo |  |  |  |  |  |

## 失败样例

- invalid JSON：
- wrong tool：
- premature final：
- verifier false positive：

## 结论

- 这次训练学到了什么：
- 数据哪里不够：
- 下一轮怎么改数据：
- 是否需要补 DPO pair：
- 是否需要改 eval：
