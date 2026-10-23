import argparse

from envarity.config_loader import load_repos, validate_repo

REPOS_PATH = "config/repos.yaml"


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
            print(f"[{repo.name}] OK — všechny branche existují")
    if any_errors:
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="envarity",
        description="Rule-based config parity auditor for multi-environment GitOps repos. Define what should match across environments; get AI-explained drift reports, not raw diffs.",
    )
    subparsers = parser.add_subparsers(dest="command")

    repos_parser = subparsers.add_parser(
        "repos", help="Práce s registrovanými repozitáři."
    )
    repos_sub = repos_parser.add_subparsers(dest="repos_command")
    repos_sub.add_parser("list", help="Vypíše registrované repozitáře.")
    repos_sub.add_parser("validate", help="Ověří, že branche v repu existují.")

    args = parser.parse_args()

    if args.command == "repos" and args.repos_command == "list":
        cmd_repos_list()
    elif args.command == "repos" and args.repos_command == "validate":
        cmd_repos_validate()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
