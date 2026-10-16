from src.cli import main

if __name__ == "__main__":
    import sys

    # this is a workaround to allow the jev command to be run as a standalone script
    argv = sys.argv[1:]
    if not argv or argv[0] != "jev":
        argv = ["jev", *argv]
    main(argv)
