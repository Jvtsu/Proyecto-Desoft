"""
PulsarLab command-line interface.

Examples
--------
    plab glitAD.par allVF.dat
    plab glitAD.par allVF.dat --port 8502
    plab glitAD.par allVF.dat --no-browser
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from . import __version__


def _existing_file(path_text: str, expected_suffix: str) -> Path:
    """Validate an input file and return its absolute path."""
    path = Path(path_text).expanduser().resolve()

    if not path.exists():
        raise argparse.ArgumentTypeError(f"File does not exist: {path}")

    if not path.is_file():
        raise argparse.ArgumentTypeError(f"Path is not a file: {path}")

    if expected_suffix and path.suffix.lower() != expected_suffix.lower():
        raise argparse.ArgumentTypeError(
            f"Expected a {expected_suffix} file, got: {path.name}"
        )

    return path


def _par_file(path_text: str) -> Path:
    return _existing_file(path_text, ".par")


def _dat_file(path_text: str) -> Path:
    # Some observational files may be saved as .txt during testing, but the
    # primary scientific workflow expects .dat.
    path = Path(path_text).expanduser().resolve()

    if not path.exists():
        raise argparse.ArgumentTypeError(f"File does not exist: {path}")

    if not path.is_file():
        raise argparse.ArgumentTypeError(f"Path is not a file: {path}")

    if path.suffix.lower() not in {".dat", ".txt"}:
        raise argparse.ArgumentTypeError(
            f"Expected a .dat or .txt file, got: {path.name}"
        )

    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="plab",
        description=(
            "Launch PulsarLab from the terminal and preload one pulsar "
            "timing-model .par file with one observational .dat file."
        ),
    )

    parser.add_argument(
        "par_file",
        type=_par_file,
        help="Path to the TEMPO/TEMPO2 .par timing-model file.",
    )

    parser.add_argument(
        "dat_file",
        type=_dat_file,
        help="Path to the observational .dat file.",
    )

    parser.add_argument(
        "--name",
        "--dataset-name",
        dest="dataset_name",
        default="Dataset 1",
        help="Display name for the preloaded dataset inside PulsarLab.",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Local Streamlit port. Default: 8501.",
    )

    parser.add_argument(
        "--host",
        default="localhost",
        help="Local host address. Default: localhost.",
    )

    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Start the server without opening a browser window automatically.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and print the Streamlit command without launching.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"PulsarLab {__version__}",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    entry_file = Path(__file__).with_name("_streamlit_entry.py").resolve()

    env = os.environ.copy()
    env["PULSARLAB_CLI_MODE"] = "1"
    env["PULSARLAB_CLI_PAR"] = str(args.par_file)
    env["PULSARLAB_CLI_DAT"] = str(args.dat_file)
    env["PULSARLAB_CLI_DATASET_NAME"] = args.dataset_name

    # Streamlit config from environment variables. This keeps the terminal
    # command self-contained and avoids requiring a .streamlit folder in the
    # user's current working directory.
    env.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    env.setdefault("STREAMLIT_THEME_BASE", "dark")
    env.setdefault("STREAMLIT_THEME_PRIMARY_COLOR", "#64B5F6")
    env.setdefault("STREAMLIT_THEME_BACKGROUND_COLOR", "#050B14")
    env.setdefault("STREAMLIT_THEME_SECONDARY_BACKGROUND_COLOR", "#0E1522")
    env.setdefault("STREAMLIT_THEME_TEXT_COLOR", "#E8EEF8")

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(entry_file),
        "--server.port",
        str(args.port),
        "--server.address",
        str(args.host),
        "--browser.gatherUsageStats",
        "false",
    ]

    if args.no_browser:
        command.extend(["--server.headless", "true"])

    print("PulsarLab")
    print("---------")
    print(f"Timing model : {args.par_file}")
    print(f"Observations : {args.dat_file}")
    print(f"Dataset name : {args.dataset_name}")
    print(f"Local URL    : http://{args.host}:{args.port}")
    print()

    if args.dry_run:
        print("Dry run: Streamlit command")
        print(" ".join(command))
        return 0

    try:
        return subprocess.call(command, env=env)
    except KeyboardInterrupt:
        print("\nPulsarLab stopped.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
