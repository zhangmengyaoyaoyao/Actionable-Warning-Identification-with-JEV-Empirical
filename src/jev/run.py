"""Entry point: python -m src.jev.run --lang java --projects bcel ..."""

from src.cli import main


if __name__ == "__main__":
    import sys

    argv = sys.argv[1:]
    if not argv or argv[0] != "jev":
        argv = ["jev", *argv]
    main(argv)
