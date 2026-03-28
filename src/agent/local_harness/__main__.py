"""Module entrypoint for the local harness."""

from __future__ import annotations

import sys

from agent.local_harness.cli import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
