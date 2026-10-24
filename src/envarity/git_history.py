import re
import subprocess

import yaml


def _read_placeholder_value(
    repo_path: str, ref: str, file_path: str, key: str
) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{ref}:{file_path}"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None  # file didn't exist at this ref

    data = yaml.safe_load(result.stdout)
    for item in data.get("placeholders", []):
        if item["name"] == key:
            return item.get("value")
    return None  # key didn't exist at this ref


def log_changes_for_key(
    repo_path: str, file_path: str, key: str, branches: list[str] | None = None
) -> list[dict]:
    revision_args = [f"origin/{b}" for b in branches] if branches else ["--all"]

    result = subprocess.run(
        [
            "git",
            "log",
            *revision_args,
            "--date=short",
            "--pretty=format:%H%x1f%an%x1f%ad%x1f%s",
            "--",
            file_path,
        ],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git log failed: {result.stderr.strip()}")

    changes = []
    for line in result.stdout.splitlines():
        commit, author, date, message = line.split("\x1f")
        before = _read_placeholder_value(repo_path, f"{commit}~1", file_path, key)
        after = _read_placeholder_value(repo_path, commit, file_path, key)
        if before != after:
            changes.append(
                {
                    "commit": commit,
                    "author": author,
                    "date": date,
                    "message": message,
                    "before": before,
                    "after": after,
                }
            )

    return changes


def extract_ticket_id(text: str) -> str | None:
    match = re.search(r"[A-Za-z]{2,}-\d+", text)
    return match.group(0) if match else None
