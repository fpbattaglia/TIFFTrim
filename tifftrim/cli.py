from __future__ import annotations

import argparse
import sys

from .trim import parse_frame_range, split_3d_tiff_into_chunks, trim_3d_tiff


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
        help="Output TIFF path (trim mode) OR output directory (split mode).",
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "-r",
        "--range",
        help='Frame range "start:end" (end exclusive). Use "10:" to go to the end.',
    )
    mode.add_argument(
        "--chunk-size",
        type=int,
        help="Split into consecutive chunks of this many frames. Writes multiple TIFFs to --output directory.",
    )

    parser.add_argument(
        "--block-size",
        type=int,
        default=3,
        help="When using --chunk-size, ensure every output file has a frame count that is a multiple of this value "
             "(default: 3). The last chunk may be truncated to satisfy this.",
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
        quiet = (not args.no_quiet)

        if args.chunk_size is not None:
            split_3d_tiff_into_chunks(
                args.input,
                args.output,
                args.chunk_size,
                block_size=args.block_size,
                quiet_tifffile_warnings=quiet,
            )
            return 0

        start, end = parse_frame_range(args.range)
        trim_3d_tiff(
            args.input,
            args.output,
            start,
            end,
            quiet_tifffile_warnings=quiet,
        )
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
