import argparse
import json
import sys

from envarity.classify import classify_diff
from envarity.config_loader import load_repos, load_rules, validate_repo
from envarity.embeddings import embed_texts, find_similar
from envarity.explain import explain_diff
from envarity.git_history import (
    build_key_histories,
    changes_to_documents,
    extract_ticket_id,
    log_all_changes,
    log_changes_for_key,
)
from envarity.git_reader import read_file_at_ref
from envarity.repo_scan import list_app_yaml_files
from envarity.report import build_matrix, pick_baseline, render_matrix
from envarity.staleness import days_behind, parse_image_dates
from envarity.yaml_diff import diff_keys, extract_placeholder_names

REPOS_PATH = "config/repos.yaml"
RULES_PATH = "config/rules.yaml"


def cmd_repos_list() -> None:
    for repo in load_repos(REPOS_PATH):
        print(f"{repo.name}  ({repo.path})")
        for env in repo.environments:
            print(f"  - {env.branch:15s} tier={env.tier}")


def cmd_repos_validate() -> None:
    any_errors = False
    for repo in load_repos(REPOS_PATH):
        errors = validate_repo(repo)
        if errors:
            any_errors = True
            for err in errors:
                print(f"[{repo.name}] ERROR: {err}")
        else:
            print(f"[{repo.name}] OK — All branches exist and are reachable.")
    if any_errors:
        raise SystemExit(1)


def cmd_check(repo_name: str, file_name: str, branch_from: str, branch_to: str) -> None:
    repo = next((r for r in load_repos(REPOS_PATH) if r.name == repo_name), None)
    if repo is None:
        raise SystemExit(f"repo '{repo_name}' not found in {REPOS_PATH}")
    rules = load_rules(RULES_PATH)

    text_from = read_file_at_ref(repo.path, f"origin/{branch_from}", file_name)
    text_to = read_file_at_ref(repo.path, f"origin/{branch_to}", file_name)

    diff = diff_keys(
        extract_placeholder_names(text_from),
        extract_placeholder_names(text_to),
    )
    result = classify_diff(diff, rules)

    print(f"Comparing {branch_from} -> {branch_to} in {file_name}\n")
    print("Expected differences:")
    for key in result["expected"]:
        print(f"  - {key}")
    print("\nSuspicious differences (FLAG):")
    for key in result["flagged"]:
        print(f"  - {key}")


def cmd_matrix(repo_name: str) -> None:
    repo = next((r for r in load_repos(REPOS_PATH) if r.name == repo_name), None)
    if repo is None:
        raise SystemExit(f"repo '{repo_name}' not found in {REPOS_PATH}")
    rules = load_rules(RULES_PATH)

    baseline = pick_baseline(repo)
    files = list_app_yaml_files(repo.path, f"origin/{baseline.branch}")
    matrix = build_matrix(repo, files, rules)
    print(render_matrix(matrix, repo.environments))


def cmd_stale_images(repo_name: str) -> None:
    repo = next((r for r in load_repos(REPOS_PATH) if r.name == repo_name), None)
    if repo is None:
        raise SystemExit(f"repo '{repo_name}' not found in {REPOS_PATH}")

    all_versions = {}
    for env in repo.environments:
        text = read_file_at_ref(repo.path, f"origin/{env.branch}", "base-images.yaml")
        all_versions[env.branch] = parse_image_dates(text)

    result = days_behind(all_versions)

    for branch, images in result.items():
        print(f"{branch}:")
        for image, days in images.items():
            if days is None:
                print(f"  {image}: missing")
            elif days == 0:
                print(f"  {image}: up to date")
            else:
                print(f"  {image}: {days} days behind")


def cmd_explain(
    repo_name: str, file_name: str, branch_from: str, branch_to: str, use_fewshot: bool
) -> None:
    repo = next((r for r in load_repos(REPOS_PATH) if r.name == repo_name), None)
    if repo is None:
        raise SystemExit(f"repo '{repo_name}' not found in {REPOS_PATH}")
    rules = load_rules(RULES_PATH)

    text_from = read_file_at_ref(repo.path, f"origin/{branch_from}", file_name)
    text_to = read_file_at_ref(repo.path, f"origin/{branch_to}", file_name)

    diff = diff_keys(
        extract_placeholder_names(text_from), extract_placeholder_names(text_to)
    )
    classified = classify_diff(diff, rules)

    key_histories = build_key_histories(
        repo.path, file_name, classified["flagged"], branches=[branch_from, branch_to]
    )

    result = explain_diff(classified, key_histories, use_fewshot=use_fewshot)
    print(json.dumps(result, indent=2))


def cmd_history(repo_name: str, key: str, app_file: str, branches: str | None) -> None:
    repo = next((r for r in load_repos(REPOS_PATH) if r.name == repo_name), None)
    if repo is None:
        raise SystemExit(f"repo '{repo_name}' not found in {REPOS_PATH}")

    branch_list = branches.split(",") if branches else None
    changes = log_changes_for_key(repo.path, app_file, key, branches=branch_list)
    if not changes:
        print(f"No value changes found for '{key}' in {app_file}.")
        return

    for c in changes:
        ticket = extract_ticket_id(c["message"])
        ticket_str = f" [{ticket}]" if ticket else ""
        print(f"{c['date']}  {c['commit'][:7]}  {c['author']}{ticket_str}")
        print(f"    {c['before']!r} -> {c['after']!r}")
        print(f"    {c['message']}")


def cmd_similar(
    repo_name: str, app_file: str, query: str, branches: str | None
) -> None:
    repo = next((r for r in load_repos(REPOS_PATH) if r.name == repo_name), None)
    if repo is None:
        raise SystemExit(f"repo '{repo_name}' not found in {REPOS_PATH}")

    branch_list = branches.split(",") if branches else None
    changes = log_all_changes(repo.path, app_file, branches=branch_list)
    documents = changes_to_documents(changes)

    if not documents:
        print("No history found to search.")
        return

    embeddings = embed_texts(documents)
    for doc, score in find_similar(query, documents, embeddings):
        print(f"{score:.3f}  {doc}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="envarity",
        description="Rule-based config parity auditor for multi-environment GitOps repos. Define what should match across environments; get AI-explained drift reports, not raw diffs.",
    )
    subparsers = parser.add_subparsers(dest="command")

    repos_parser = subparsers.add_parser(
        "repos", help="Work with registered repositories."
    )
    repos_sub = repos_parser.add_subparsers(dest="repos_command")
    repos_sub.add_parser("list", help="List registered repositories.")
    repos_sub.add_parser("validate", help="Verify that branches in the repo exist.")

    check_parser = subparsers.add_parser(
        "check",
        help="Compares two branches of a repo and reports differences in placeholders.",
    )

    check_parser.add_argument("repo_name")
    check_parser.add_argument("--file", required=True)
    check_parser.add_argument("--from", dest="branch_from", required=True)
    check_parser.add_argument("--to", dest="branch_to", required=True)

    matrix_parser = subparsers.add_parser(
        "matrix", help="Matrix report across all apps and environments."
    )
    matrix_parser.add_argument("repo_name")

    stale_parser = subparsers.add_parser(
        "stale-images", help="Show base image staleness across environments."
    )
    stale_parser.add_argument("repo_name")

    explain_parser = subparsers.add_parser(
        "explain", help="Use an LLM to explain and risk-rate a diff."
    )
    explain_parser.add_argument("repo_name")
    explain_parser.add_argument("--file", required=True)
    explain_parser.add_argument("--from", dest="branch_from", required=True)
    explain_parser.add_argument("--to", dest="branch_to", required=True)
    explain_parser.add_argument(
        "--no-fewshot", action="store_true", help="Disable few-shot examples."
    )

    history_parser = subparsers.add_parser(
        "history", help="Show real value-change history for a placeholder key."
    )
    history_parser.add_argument("repo_name")
    history_parser.add_argument("key")
    history_parser.add_argument("--app", dest="app_file", required=True)
    history_parser.add_argument(
        "--branches",
        help="Comma-separated branches to scope the search to (default: all).",
    )

    similar_parser = subparsers.add_parser(
        "similar", help="Semantic search over a file's change history."
    )
    similar_parser.add_argument("repo_name")
    similar_parser.add_argument("query")
    similar_parser.add_argument("--app", dest="app_file", required=True)
    similar_parser.add_argument("--branches")

    args = parser.parse_args()

    try:
        if args.command == "repos" and args.repos_command == "list":
            cmd_repos_list()
        elif args.command == "repos" and args.repos_command == "validate":
            cmd_repos_validate()
        elif args.command == "check":
            cmd_check(args.repo_name, args.file, args.branch_from, args.branch_to)
        elif args.command == "matrix":
            cmd_matrix(args.repo_name)
        elif args.command == "stale-images":
            cmd_stale_images(args.repo_name)
        elif args.command == "explain":
            cmd_explain(
                args.repo_name,
                args.file,
                args.branch_from,
                args.branch_to,
                not args.no_fewshot,
            )
        elif args.command == "history":
            cmd_history(args.repo_name, args.key, args.app_file, args.branches)
        elif args.command == "similar":
            cmd_similar(args.repo_name, args.app_file, args.query, args.branches)
        else:
            parser.print_help()
    except FileNotFoundError as e:
        if e.filename in (REPOS_PATH, RULES_PATH):
            example = e.filename.replace(".yaml", ".example.yaml")
            print(f"Error: {e.filename} not found.", file=sys.stderr)
            print(f"  Run: cp {example} {e.filename}", file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
