import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COURSE_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(COURSE_ROOT / "toy_project"))

from eval_agent import build_messages, extract_action, run_rule_based_agent
from prepare_dataset import build_dpo_records, build_sft_records, load_jsonl, validate_sft_messages


def test_prepare_dataset_builds_sft_and_dpo_records():
    raw_path = COURSE_ROOT / "toy_project" / "data" / "trajectories_raw.jsonl"
    trajectories = load_jsonl(raw_path)

    sft = build_sft_records(trajectories)
    dpo = build_dpo_records(trajectories)

    assert len(sft) == 5
    assert len(dpo) == 5
    assert sft[0]["source_task_id"].startswith("doc_")
    assert validate_sft_messages(sft[0]["messages"]) == []
    assert {"prompt", "chosen", "rejected", "source_task_id", "chosen_score", "rejected_score"} <= set(dpo[0])
    assert dpo[0]["chosen_score"] > dpo[0]["rejected_score"]


def test_extract_action_parses_json_and_final():
    action = extract_action('{"action":"search_text","arguments":{"query":"GRPO"}}')
    final = extract_action("Final: 已完成。")

    assert action.kind == "action"
    assert action.name == "search_text"
    assert action.arguments == {"query": "GRPO"}
    assert final.kind == "final"
    assert final.final == "已完成。"


def test_rule_based_eval_runner_completes_toy_task():
    task = {
        "task_id": "doc_001",
        "prompt": "找到 GRPO 适合什么任务。",
        "query": "GRPO",
        "answer_contains": ["GRPO", "可验证", "reward"],
    }

    result = run_rule_based_agent(task, max_steps=4)

    assert result["score"] == 1.0
    assert result["final_status"] == "success"
    assert result["parse_errors"] == 0
    assert result["invalid_actions"] == 0
    assert result["steps"] >= 2


def test_build_messages_uses_chat_roles():
    task = {"prompt": "找到 GRPO 适合什么任务。"}
    messages = build_messages(task, [{"assistant": {"action": "search_text", "arguments": {"query": "GRPO"}}, "tool": []}])

    assert [message["role"] for message in messages] == ["system", "user", "assistant", "tool"]
