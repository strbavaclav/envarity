from pathlib import Path

from mcp.server import MCPServer

from envarity.classify import classify_diff
from envarity.config_loader import load_repos, load_rules
from envarity.embeddings import embed_texts, find_similar
from envarity.git_history import (
    changes_to_documents,
    log_all_changes,
    summarize_key_history,
)
from envarity.git_reader import read_file_at_ref
from envarity.yaml_diff import diff_keys, extract_placeholder_names

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPOS_PATH = str(PROJECT_ROOT / "config" / "repos.yaml")
RULES_PATH = str(PROJECT_ROOT / "config" / "rules.yaml")

mcp = MCPServer("envarity")


def _resolve_repo(repo_name: str):
    repo = next((r for r in load_repos(REPOS_PATH) if r.name == repo_name), None)
    if repo is None:
        raise ValueError(f"repo '{repo_name}' not found in {REPOS_PATH}")
    return repo


@mcp.tool()
def get_diff(repo_name: str, file: str, branch_from: str, branch_to: str) -> dict:
    """Get the classified placeholder key diff between two environments of a registered repo."""
    repo = _resolve_repo(repo_name)
    rules = load_rules(RULES_PATH)
    text_from = read_file_at_ref(repo.path, f"origin/{branch_from}", file)
    text_to = read_file_at_ref(repo.path, f"origin/{branch_to}", file)
    diff = diff_keys(
        extract_placeholder_names(text_from), extract_placeholder_names(text_to)
    )
    return classify_diff(diff, rules)


@mcp.tool()
def get_key_history(
    repo_name: str, file: str, branch_from: str, branch_to: str, key: str
) -> dict:
    """Get the real change history (count of changes + ticket IDs) for one placeholder key."""
    repo = _resolve_repo(repo_name)
    summary = summarize_key_history(
        repo.path, file, key, branches=[branch_from, branch_to]
    )
    return {"key": key, "history": summary}


@mcp.tool()
def search_similar(
    repo_name: str, file: str, branch_from: str, branch_to: str, query: str
) -> dict:
    """Semantic search over a file's change history using a natural-language description."""
    repo = _resolve_repo(repo_name)
    changes = log_all_changes(repo.path, file, branches=[branch_from, branch_to])
    documents = changes_to_documents(changes)
    if not documents:
        return {"results": []}
    embeddings = embed_texts(documents)
    results = find_similar(query, documents, embeddings, top_k=3)
    return {"results": [{"text": doc, "score": score} for doc, score in results]}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
