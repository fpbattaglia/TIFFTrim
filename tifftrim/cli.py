from __future__ import annotations

import argparse
import sys

from .trim import parse_frame_range, trim_3d_tiff


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tifftrim",
        description="Trim a 3D TIFF stack while preserving TIFF tags/metadata per page.",
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input TIFF path",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output TIFF path",
    )
    parser.add_argument(
        "-r",
        "--range",
        required=True,
        help='Frame range "start:end" (end exclusive). Use "10:" to go to the end.',
    )
    parser.add_argument(
        "--no-quiet",
        action="store_true",
        help="Do not suppress tifffile warnings on stderr.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        start, end = parse_frame_range(args.range)
        trim_3d_tiff(
            args.input,
            args.output,
            start,
            end,
            quiet_tifffile_warnings=(not args.no_quiet),
        )
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
