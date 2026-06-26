"""CLI entry point for the antenna calculator registry.

Per-type formulas live in calculators/*.py (one module per antenna type,
self-registering via @register). This file just dispatches and prints.
"""

import calculators  # noqa: F401 -- side effect: registers all calculator types
from data_store import BANDS_MHZ
from format_text import format_summary
from registry import REGISTRY, design


def _build_argparser():
    import argparse

    parser = argparse.ArgumentParser(description="HAM antenna calculator")
    parser.add_argument(
        "antenna_type", nargs="?", default="vertical_quarter_wave",
        help=f"Antenna type, one of: {', '.join(REGISTRY)}",
    )
    parser.add_argument("band", nargs="?", default="20m", help=f"HAM band, one of: {', '.join(BANDS_MHZ)}")
    parser.add_argument(
        "--units", choices=["metric", "imperial"], default="metric",
        help="Display units for lengths (default: metric)",
    )
    parser.add_argument(
        "--lang", choices=["en", "nl"], default="en",
        help="Language for output text (default: en)",
    )
    return parser


if __name__ == "__main__":
    args = _build_argparser().parse_args()
    d = design(args.antenna_type, args.band, lang=args.lang)
    print(format_summary(d, units=args.units, lang=args.lang))
