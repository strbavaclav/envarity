import subprocess


def read_file_at_ref(repo_path: str, ref: str, file_path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{ref}:{file_path}"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise FileNotFoundError(
            f"{file_path} nenalezen na {ref}: {result.stderr.strip()}"
        )
    return result.stdout
