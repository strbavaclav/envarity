from envarity.classify import classify_diff
from envarity.config_models import RepoConfig, Rule
from envarity.git_reader import read_file_at_ref
from envarity.yaml_diff import diff_keys, extract_placeholder_names


def pick_baseline(repo: RepoConfig):
    for env in repo.environments:
        if env.tier == "production":
            return env
    return repo.environments[-1]


def build_matrix(repo: RepoConfig, files: list[str], rules: list[Rule]) -> dict:
    baseline = pick_baseline(repo)
    matrix: dict[str, dict[str, dict]] = {}

    for file_name in files:
        matrix[file_name] = {}
        baseline_text = read_file_at_ref(
            repo.path, f"origin/{baseline.branch}", file_name
        )
        baseline_keys = extract_placeholder_names(baseline_text)

        for env in repo.environments:
            try:
                env_text = read_file_at_ref(
                    repo.path, f"origin/{env.branch}", file_name
                )
            except FileNotFoundError:
                matrix[file_name][env.branch] = {"keys": 0, "flagged": None}
                continue

            env_keys = extract_placeholder_names(env_text)
            diff = diff_keys(baseline_keys, env_keys)
            classified = classify_diff(diff, rules)
            matrix[file_name][env.branch] = {
                "keys": len(env_keys),
                "flagged": len(classified["flagged"]),
            }

    return matrix


def render_matrix(matrix: dict, environments: list) -> str:
    branch_names = [env.branch for env in environments]
    col_width = max(len(b) for b in branch_names) + 2

    lines = ["file".ljust(24) + "".join(b.ljust(col_width) for b in branch_names)]

    for file_name, by_branch in matrix.items():
        row = file_name.ljust(24)
        for branch in branch_names:
            cell = by_branch.get(branch)
            if cell is None or cell["flagged"] is None:
                text = "missing"
            else:
                text = f"{cell['keys']}k/{cell['flagged']}f"
            row += text.ljust(col_width)
        lines.append(row)

    return "\n".join(lines)
