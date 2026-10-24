import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

STALE_THRESHOLD = timedelta(minutes=15)


def _format_age(age: timedelta) -> str:
    hours = age.total_seconds() / 3600
    if hours < 1:
        return f"{int(age.total_seconds() / 60)} minutes"
    if hours < 48:
        return f"{hours:.1f} hours"
    return f"{hours / 24:.1f} days"


def check_freshness(repo_path: str) -> None:
    fetch_head = Path(repo_path) / ".git" / "FETCH_HEAD"
    if not fetch_head.exists():
        return

    age = datetime.now() - datetime.fromtimestamp(fetch_head.stat().st_mtime)
    if age <= STALE_THRESHOLD:
        return

    print(
        f"Warning: {repo_path} was last fetched {_format_age(age)} ago.",
        file=sys.stderr,
    )
    answer = input("Fetch now? [Y/n] ").strip().lower()
    if answer not in ("", "y", "yes"):
        return

    result = subprocess.run(
        ["git", "fetch", "--all"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    updates = result.stderr.strip()
    if updates:
        print(f"Fetched new data:\n{updates}", file=sys.stderr)
    else:
        print("Already up to date — no new data on the remote.", file=sys.stderr)
