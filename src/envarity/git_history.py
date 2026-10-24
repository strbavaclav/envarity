import re
import subprocess

import yaml


def _read_placeholders(repo_path: str, ref: str, file_path: str) -> dict[str, str]:
    result = subprocess.run(
        ["git", "show", f"{ref}:{file_path}"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {}
    data = yaml.safe_load(result.stdout)
    return {item["name"]: item.get("value") for item in data.get("placeholders", [])}


def _read_placeholder_value(
    repo_path: str, ref: str, file_path: str, key: str
) -> str | None:
    return _read_placeholders(repo_path, ref, file_path).get(key)


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


def log_all_changes(
    repo_path: str, file_path: str, branches: list[str] | None = None
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
        before = _read_placeholders(repo_path, f"{commit}~1", file_path)
        after = _read_placeholders(repo_path, commit, file_path)

        changed_keys = {
            key: (before.get(key), after.get(key))
            for key in set(before) | set(after)
            if before.get(key) != after.get(key)
        }

        if changed_keys:
            changes.append(
                {
                    "commit": commit,
                    "author": author,
                    "date": date,
                    "message": message,
                    "changed_keys": changed_keys,
                }
            )

    return changes


def _describe_change(key: str, before: str | None, after: str | None) -> str:
    if before is None:
        return f"added {key} with value {after!r}"
    if after is None:
        return f"removed {key} (was {before!r})"
    return f"changed {key} from {before!r} to {after!r}"


def changes_to_documents(changes: list[dict]) -> list[str]:
    documents = []
    for c in changes:
        descriptions = [
            _describe_change(key, old, new)
            for key, (old, new) in c["changed_keys"].items()
        ]
        documents.append(f"{c['message']}. This change {', '.join(descriptions)}.")
    return documents


def extract_ticket_id(text: str) -> str | None:
    match = re.search(r"[A-Za-z]{2,}-\d+", text)
    return match.group(0) if match else None
