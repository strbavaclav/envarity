import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="envdrift",
        description="Diagnostika config promotion mezi environment branchemi.",
    )
    parser.parse_args()


if __name__ == "__main__":
    main()
