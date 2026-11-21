"""Convenience entry point: `python main.py --repo . [--offline]`."""

from release_brief.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
