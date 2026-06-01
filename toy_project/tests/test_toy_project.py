import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import list_files, read_file, search_text
from verifier import verify_answer
from build_sft_dataset import trajectory_to_sft
from build_dpo_dataset import build_pairs


def test_tools_list_read_and_search_corpus():
    files = list_files()

    assert "lesson_06.md" in files
    assert "training_recipes.md" in files
    assert "GRPO" in read_file("lesson_06.md")

    matches = search_text("chosen")
    assert any(match["path"] == "training_recipes.md" for match in matches)


def test_verifier_requires_all_expected_terms():
    task = {"answer_contains": ["GRPO", "可验证", "reward"]}

    assert verify_answer(task, "GRPO 适合可验证任务，因为可以用 reward 比较多条轨迹。") == 1.0
    assert verify_answer(task, "GRPO 是一种训练方法。") == 0.0


def test_trajectory_to_sft_preserves_tool_messages():
    trajectory = {
        "task": "找到 GRPO 适合什么任务。",
        "steps": [
            {
                "assistant": {"action": "search_text", "arguments": {"query": "GRPO"}},
                "tool": [{"path": "lesson_06.md", "line": 1, "text": "GRPO 适合可验证任务。"}],
            }
        ],
        "final": "GRPO 适合可验证任务。",
    }

    sample = trajectory_to_sft(trajectory)

    assert sample["messages"][0]["role"] == "user"
    assert sample["messages"][1]["role"] == "assistant"
    assert sample["messages"][1]["content"] is None
    assert sample["messages"][1]["tool_calls"][0]["function"]["name"] == "search_text"
    assert json.loads(sample["messages"][1]["tool_calls"][0]["function"]["arguments"]) == {"query": "GRPO"}
    assert sample["messages"][2]["role"] == "tool"
    assert sample["messages"][2]["tool_call_id"] == sample["messages"][1]["tool_calls"][0]["id"]
    assert sample["messages"][-1]["content"] == "GRPO 适合可验证任务。"


def test_build_pairs_uses_highest_score_as_chosen():
    trajectories = [
        {"task_id": "doc_001", "task": "找到 GRPO 适合什么任务。", "final": "bad", "score": 0.0, "steps": []},
        {
            "task_id": "doc_001",
            "task": "找到 GRPO 适合什么任务。",
            "final": "GRPO 适合可验证任务。",
            "score": 1.0,
            "steps": [
                {"assistant": {"action": "search_text", "arguments": {"query": "GRPO"}}, "tool": []}
            ],
        },
    ]

    pairs = build_pairs(trajectories)

    assert len(pairs) == 1
    assert "GRPO 适合可验证任务" in pairs[0]["chosen"][-1]["content"]
    assert pairs[0]["rejected"] == [{"role": "assistant", "content": "bad"}]
