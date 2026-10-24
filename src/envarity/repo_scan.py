import subprocess


def list_app_yaml_files(repo_path: str, ref: str) -> list[str]:
    result = subprocess.run(
        ["git", "ls-tree", "--name-only", ref],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"failed to list files at {ref}: {result.stderr.strip()}")

    # TODO: This is a temporary workaround to exclude certain files from the list.
    excluded = {"common.yaml", "base-images.yaml"}
    return [
        name
        for name in result.stdout.splitlines()
        if name.endswith(".yaml") and name not in excluded
    ]
