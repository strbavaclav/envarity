import json
from pathlib import Path

from openai.types.chat import ChatCompletionMessageParam

from envarity.classify import classify_diff
from envarity.config_loader import load_repos, load_rules
from envarity.git_reader import read_file_at_ref
from envarity.yaml_diff import diff_keys, extract_placeholder_names

FEWSHOTS_DIR = "config/few_shots"
REPOS_PATH = "config/repos.yaml"
RULES_PATH = "config/rules.yaml"


def build_fewshot_messages() -> list[ChatCompletionMessageParam]:
    repos = load_repos(REPOS_PATH)
    rules = load_rules(RULES_PATH)
    messages: list[ChatCompletionMessageParam] = []

    for path in sorted(Path(FEWSHOTS_DIR).glob("*.json")):
        if path.name.endswith(".example.json"):
            continue

        case = json.loads(path.read_text())
        repo = next(r for r in repos if r.name == case["repo"])

        text_from = read_file_at_ref(repo.path, f"origin/{case['from']}", case["file"])
        text_to = read_file_at_ref(repo.path, f"origin/{case['to']}", case["file"])
        diff = diff_keys(
            extract_placeholder_names(text_from),
            extract_placeholder_names(text_to),
        )
        classified = classify_diff(diff, rules)

        answer = {
            "summary": case["summary"],
            "risk": case["expected_risk"],
            "reasoning": case["reasoning"],
        }

        messages.append({"role": "user", "content": json.dumps(classified)})
        messages.append({"role": "assistant", "content": json.dumps(answer)})

    return messages
