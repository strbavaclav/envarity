import subprocess
from pathlib import Path

import yaml

from envarity.config_models import RepoConfig, Rule


def load_repos(path: str) -> list[RepoConfig]:
    data = yaml.safe_load(Path(path).read_text())
    return [RepoConfig(**entry) for entry in data["repos"]]


def load_rules(path: str) -> list[Rule]:
    data = yaml.safe_load(Path(path).read_text())
    return [Rule(**entry) for entry in data["rules"]]


def validate_repo(repo: RepoConfig) -> list[str]:
    errors = []
    for env in repo.environments:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"origin/{env.branch}"],
            cwd=repo.path,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            errors.append(
                f"branch '{env.branch}' (tier={env.tier}) not found in {repo.path}"
            )
    return errors
