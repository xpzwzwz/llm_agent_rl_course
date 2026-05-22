import argparse
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
COURSE_ROOT = ROOT.parent
TOY_ROOT = COURSE_ROOT / "toy_project"
DEFAULT_RAW = TOY_ROOT / "data" / "trajectories_raw.jsonl"
DEFAULT_TASKS = TOY_ROOT / "data" / "tasks.jsonl"
DEFAULT_OUT = ROOT / "data"

HELDOUT_TASKS = [
    {
        "task_id": "heldout_001",
        "prompt": "GRPO 更适合哪类可以自动打分的任务？",
        "query": "GRPO",
        "answer_contains": ["GRPO", "可验证", "reward"],
    },
    {
        "task_id": "heldout_002",
        "prompt": "DPO 训练样本里通常要比较哪两个字段？",
        "query": "DPO",
        "answer_contains": ["prompt", "chosen", "rejected"],
    },
    {
        "task_id": "heldout_003",
        "prompt": "举一个 agent 训练中 reward hacking 的代码任务例子。",
        "query": "reward hacking",
        "answer_contains": ["删除测试", "reward", "任务"],
    },
]


def load_jsonl(path):
    with Path(path).open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def validate_sft_messages(messages):
    errors = []
    roles = [message.get("role") for message in messages]
    if "user" not in roles:
        errors.append("missing_user")
    if "assistant" not in roles:
        errors.append("missing_assistant")
    if "tool" not in roles:
        errors.append("missing_tool")
    if not any(message.get("role") == "assistant" and message.get("content", "").startswith("Final:") for message in messages):
        errors.append("missing_final")
    for index, message in enumerate(messages):
        if not isinstance(message.get("content"), str) or not message["content"].strip():
            errors.append(f"empty_content_{index}")
    return errors


def trajectory_to_messages(trajectory):
    messages = [{"role": "user", "content": trajectory["task"]}]
    for step in trajectory["steps"]:
        messages.append({"role": "assistant", "content": json.dumps(step["assistant"], ensure_ascii=False)})
        messages.append({"role": "tool", "content": json.dumps(step["tool"], ensure_ascii=False)})
    messages.append({"role": "assistant", "content": f"Final: {trajectory['final']}"})
    return messages


def build_sft_records(trajectories):
    records = []
    for trajectory in trajectories:
        if trajectory.get("score") != 1.0:
            continue
        messages = trajectory_to_messages(trajectory)
        errors = validate_sft_messages(messages)
        if errors:
            raise ValueError(f"{trajectory['task_id']} invalid SFT sample: {errors}")
        records.append(
            {
                "messages": messages,
                "source_task_id": trajectory["task_id"],
                "source_score": trajectory["score"],
                "quality_grade": "A",
            }
        )
    return records


def render_trajectory(trajectory):
    parts = []
    for step in trajectory["steps"]:
        parts.append(f"Action: {json.dumps(step['assistant'], ensure_ascii=False)}")
        parts.append(f"Result: {json.dumps(step['tool'], ensure_ascii=False)}")
    parts.append(f"Final: {trajectory['final']}")
    return "\n".join(parts)


def build_dpo_records(trajectories):
    by_task = defaultdict(list)
    for trajectory in trajectories:
        by_task[trajectory["task_id"]].append(trajectory)

    records = []
    for task_id, items in sorted(by_task.items()):
        ordered = sorted(items, key=lambda item: item.get("score", 0.0), reverse=True)
        chosen = ordered[0]
        rejected = ordered[-1]
        if chosen.get("score", 0.0) <= rejected.get("score", 0.0):
            continue
        records.append(
            {
                "prompt": chosen["task"],
                "chosen": render_trajectory(chosen),
                "rejected": render_trajectory(rejected),
                "source_task_id": task_id,
                "chosen_score": chosen.get("score", 0.0),
                "rejected_score": rejected.get("score", 0.0),
            }
        )
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw_path", default=str(DEFAULT_RAW))
    parser.add_argument("--tasks_path", default=str(DEFAULT_TASKS))
    parser.add_argument("--output_dir", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    trajectories = load_jsonl(args.raw_path)
    train_tasks = load_jsonl(args.tasks_path)
    eval_tasks = train_tasks + HELDOUT_TASKS
    sft = build_sft_records(trajectories)
    dpo = build_dpo_records(trajectories)

    write_jsonl(output_dir / "train_sft.jsonl", sft)
    write_jsonl(output_dir / "train_dpo.jsonl", dpo)
    write_jsonl(output_dir / "eval_tasks.jsonl", eval_tasks)
    write_jsonl(output_dir / "heldout_eval_tasks.jsonl", HELDOUT_TASKS)

    print(f"wrote {len(sft)} SFT samples to {output_dir / 'train_sft.jsonl'}")
    print(f"wrote {len(dpo)} DPO pairs to {output_dir / 'train_dpo.jsonl'}")
    print(f"wrote {len(eval_tasks)} eval tasks to {output_dir / 'eval_tasks.jsonl'}")
    print(f"wrote {len(HELDOUT_TASKS)} held-out eval tasks to {output_dir / 'heldout_eval_tasks.jsonl'}")


if __name__ == "__main__":
    main()
