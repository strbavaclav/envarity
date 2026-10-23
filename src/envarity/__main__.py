import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="envarity",
        description="Rule-based config parity auditor for multi-environment GitOps repos. Define what should match across environments; get AI-explained drift reports, not raw diffs.",
    )
    parser.parse_args()


if __name__ == "__main__":
    main()
