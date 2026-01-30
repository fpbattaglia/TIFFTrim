# TIFFTrim (tifftrim)

A small command-line tool + Python module to **trim 3D TIFF stacks** (shape `[frames, y, x]`) while **preserving TIFF tags/metadata per page** as much as `tifffile` allows.

## Features

- Trims a frame range from a multi-page (3D) TIFF stack
- Attempts to preserve per-page:
  - TIFF tags via `extratags`
  - `description`, `datetime`, `resolution`, `compression`, `photometric`, `planarconfig`
  - `software` tag (important for some acquisition pipelines)

## Installation

From the project root:

```aiignore
bash python -m pip install -e .
```

This installs a console script named `tifftrim`.

## Command line usage

### Trim a specific range (end exclusive)

Keep frames `0..999`:

```aiignore
bash tifftrim -i /path/to/input.tif -o /path/to/output.tif -r 0:1000
```


### Trim from a start frame to the end

Keep frames `500..end`:

```aiignore
bash tifftrim -i /path/to/input.tif -o /path/to/output.tif -r 500:
```


### Show tifffile warnings (disable quiet mode)
```aiignore
bash tifftrim -i /path/to/input.tif -o /path/to/output.tif -r 0:100 --no-quiet
```


## Range format

The `--range` argument uses:

- `start:end`
- `start` is **inclusive**
- `end` is **exclusive**
- `end` can be omitted to mean “to the end” (e.g. `10:`)

Examples:

- `0:100` means frames 0 through 99
- `10:` means frames 10 through the last frame

## Python API

You can call the core function directly:

```
python from tifftrim import trim_3d_tiff
trim_3d_tiff
```


## Notes / limitations

- The tool expects the TIFF to load as a **3D array** (`tifffile.TiffFile(...).asarray()`), i.e. `[frames, y, x]`. If your file loads with a different shape (e.g. extra channels), you may need to adapt the logic.
- Some tags may be skipped if they can’t be serialized in `extratags` format.

## Development

Project entry point:

- CLI: `tifftrim/cli.py`
- Core trimming logic: `tifftrim/trim.py`
- Packaging: `setup.py`
