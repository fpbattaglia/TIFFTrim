from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path
from typing import Optional, Tuple, Union

import tifffile
try:
    from tqdm.auto import tqdm
except Exception:  # pragma: no cover
    tqdm = None
    print("tqdm not found, disabling progress bar")


_AUTO_HANDLED_TAG_CODES = {
    256,  # ImageWidth
    257,  # ImageLength
    258,  # BitsPerSample
    259,  # Compression
    262,  # PhotometricInterpretation
    277,  # SamplesPerPixel
    278,  # RowsPerStrip
    279,  # StripByteCounts
    284,  # PlanarConfiguration
    317,  # Predictor
    320,  # ColorMap
    339,  # SampleFormat
}


def trim_3d_tiff(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    start_frame: int,
    end_frame: Optional[int],
    *,
    quiet_tifffile_warnings: bool = True,
    show_progress: bool = True,
) -> None:
    """
    Trim a 3D TIFF stack [frames, height, width] while preserving per-page tags/metadata.

    Frame range semantics:
        - start_frame is inclusive
        - end_frame is exclusive
        - if end_frame is None, it trims until the last frame
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    orig_err = sys.stderr
    if quiet_tifffile_warnings:
        sys.stderr = StringIO()

    try:
        imagej_metadata = None

        with tifffile.TiffFile(str(input_path)) as tiff:
            data = tiff.asarray()

            if len(data.shape) != 3:
                raise ValueError(f"Expected a 3D TIFF [frames, y, x], got shape {data.shape}")

            n_frames = data.shape[0]

            if end_frame is None:
                end_frame = n_frames

            if start_frame < 0 or start_frame > n_frames:
                raise ValueError(f"Invalid start_frame={start_frame}. File has {n_frames} frames.")

            if end_frame < 0 or end_frame > n_frames:
                raise ValueError(f"Invalid end_frame={end_frame}. File has {n_frames} frames.")

            if start_frame >= end_frame:
                raise ValueError("start_frame must be < end_frame")

            original_pages = []
            for page in tiff.pages[start_frame:end_frame]:
                extratags = []
                for tag in page.tags.values():
                    if int(tag.code) in _AUTO_HANDLED_TAG_CODES:
                        continue

                    try:
                        if isinstance(tag.value, (tuple, list)):
                            value = list(tag.value)
                        else:
                            value = tag.value

                        extratags.append(
                            (
                                int(tag.code),
                                tag.dtype,
                                tag.count,
                                value,
                                False,
                            )
                        )
                    except Exception:
                        # Skip tags that can't be serialized by tifffile extratags
                        continue

                original_pages.append(
                    {
                        "extratags": extratags,
                        "description": page.description,
                        "datetime": page.datetime,
                        "resolution": page.resolution,
                        "compression": page.compression,
                        "photometric": page.photometric,
                        "planarconfig": page.planarconfig,
                        "software": page.software,
                    }
                )

            trimmed_data = data[start_frame:end_frame]

            with tifffile.TiffWriter(str(output_path), bigtiff=tiff.is_bigtiff) as tw:
                iterable = zip(trimmed_data, original_pages)
                if tqdm is not None:
                    iterable = tqdm(
                        iterable,
                        total=len(original_pages),
                        desc="Writing frames",
                        unit="frame",
                        disable=not show_progress,
                    )

                for idx, (frame, page_info) in enumerate(iterable):
                    tw.write(
                        frame,
                        description=page_info["description"],
                        datetime=page_info["datetime"],
                        resolution=page_info["resolution"],
                        compression=page_info["compression"],
                        photometric=page_info["photometric"],
                        planarconfig=page_info["planarconfig"],
                        extratags=page_info["extratags"],
                        metadata=imagej_metadata if idx == 0 else None,
                        software=page_info["software"],
                    )
    finally:
        if quiet_tifffile_warnings:
            sys.stderr = orig_err


def split_3d_tiff_into_chunks(
    input_path: Union[str, Path],
    output_dir: Union[str, Path],
    chunk_size: int,
    *,
    quiet_tifffile_warnings: bool = True,
    show_progress: bool = True,
) -> list[Path]:
    """
    Split a 3D TIFF stack [frames, y, x] into consecutive chunks of chunk_size frames.

    Output files are written to output_dir and named:
        <input_stem>_frames_<start>_<end>.tif
    where end is exclusive.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")

    input_path = Path(input_path)
    output_dir = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    orig_err = sys.stderr
    if quiet_tifffile_warnings:
        sys.stderr = StringIO()

    written: list[Path] = []
    try:
        imagej_metadata = None

        with tifffile.TiffFile(str(input_path)) as tiff:
            data = tiff.asarray()

            if len(data.shape) != 3:
                raise ValueError(f"Expected a 3D TIFF [frames, y, x], got shape {data.shape}")

            n_frames = data.shape[0]
            if n_frames == 0:
                return []

            ranges = [(start, min(start + chunk_size, n_frames)) for start in range(0, n_frames, chunk_size)]

            range_iter = ranges
            if tqdm is not None:
                range_iter = tqdm(
                    ranges,
                    total=len(ranges),
                    desc="Writing chunks",
                    unit="chunk",
                    disable=not show_progress,
                )

            for start, end in range_iter:
                out_path = output_dir / f"{input_path.stem}_frames_{start}_{end}.tif"

                original_pages = []
                for page in tiff.pages[start:end]:
                    extratags = []
                    for tag in page.tags.values():
                        if int(tag.code) in _AUTO_HANDLED_TAG_CODES:
                            continue

                        try:
                            if isinstance(tag.value, (tuple, list)):
                                value = list(tag.value)
                            else:
                                value = tag.value

                            extratags.append(
                                (
                                    int(tag.code),
                                    tag.dtype,
                                    tag.count,
                                    value,
                                    False,
                                )
                            )
                        except Exception:
                            continue

                    original_pages.append(
                        {
                            "extratags": extratags,
                            "description": page.description,
                            "datetime": page.datetime,
                            "resolution": page.resolution,
                            "compression": page.compression,
                            "photometric": page.photometric,
                            "planarconfig": page.planarconfig,
                            "software": page.software,
                        }
                    )

                chunk_data = data[start:end]

                with tifffile.TiffWriter(str(out_path), bigtiff=tiff.is_bigtiff) as tw:
                    for idx, (frame, page_info) in enumerate(zip(chunk_data, original_pages)):
                        tw.write(
                            frame,
                            description=page_info["description"],
                            datetime=page_info["datetime"],
                            resolution=page_info["resolution"],
                            compression=page_info["compression"],
                            photometric=page_info["photometric"],
                            planarconfig=page_info["planarconfig"],
                            extratags=page_info["extratags"],
                            metadata=imagej_metadata if idx == 0 else None,
                            software=page_info["software"],
                        )

                written.append(out_path)

        return written
    finally:
        if quiet_tifffile_warnings:
            sys.stderr = orig_err


def parse_frame_range(range_text: str) -> Tuple[int, Optional[int]]:
    """
    Parse a frame range in the form:
        "start:end" where end is exclusive, end may be empty (e.g. "10:")

    Examples:
        "0:100" -> (0, 100)
        "10:"   -> (10, None)
    """
    text = range_text.strip()
    if ":" not in text:
        raise ValueError('Range must be in the form "start:end" (end exclusive), e.g. "0:100" or "10:"')

    start_str, end_str = text.split(":", 1)
    start_str = start_str.strip()
    end_str = end_str.strip()

    if start_str == "":
        raise ValueError('Range "start:end" requires a start value (e.g. "0:100")')

    start = int(start_str)
    end = None if end_str == "" else int(end_str)
    return start, end
