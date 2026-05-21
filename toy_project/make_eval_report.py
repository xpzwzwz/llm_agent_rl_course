import json
from collections import Counter
from pathlib import Path

from build_sft_dataset import load_trajectories


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "reports" / "eval_toy.md"


def summarize(trajectories):
    total = len(trajectories)
    successes = sum(1 for item in trajectories if item.get("score") == 1.0)
    variants = Counter(item["variant"] for item in trajectories)
    return {
        "total": total,
        "successes": successes,
        "success_rate": successes / total if total else 0.0,
        "variants": variants,
    }


def main():
    trajectories = load_trajectories()
    summary = summarize(trajectories)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Toy Agent Eval Report",
        "",
        f"num_trajectories: {summary['total']}",
        f"successes: {summary['successes']}",
        f"success_rate: {summary['success_rate']:.2f}",
        "",
        "## Variants",
        "",
    ]
    for name, count in sorted(summary["variants"].items()):
        lines.append(f"- {name}: {count}")
    lines.extend(["", "## Example Failure", ""])
    failure = next((item for item in trajectories if item.get("score") == 0.0), None)
    if failure:
        lines.append(f"- task_id: {failure['task_id']}")
        lines.append(f"- final: {failure['final']}")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

