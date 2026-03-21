"""Entry point for `python -m researcher <subcommand>`."""
import sys


def main() -> None:
    """Dispatch to CLI subcommands."""
    try:
        from researcher import cli  # noqa: PLC0415
        cli.main()
    except ImportError:
        print("researcher: no subcommand specified", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
