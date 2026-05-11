#!/usr/bin/env python3
"""
Convert raw LAZ/LAS files to tiled COPC.

Reads from 01_raw, optionally drops user-defined ExtraBytes, optionally
thins via a voxel filter, splits into fixed-size tiles (default 250 m),
and writes COPC files named {site}_{Xmin}_{Ymin}.copc.laz to 02_input.

Based on:
    https://github.com/MAAP-Project/geotrees-demo/blob/main/convert_las_to_copc.py

Strategy for ExtraBytes handling (portable across PDAL versions):
  - To DROP extras: don't read them. readers.las by default does NOT load
    extra dims from the file's ExtraBytes VLR unless extra_dims is set.
    We also use forward="header" so the ExtraBytes VLR isn't carried over.
    `extra_dims` is omitted on writers.copc entirely (some PDAL builds
    reject an empty value).
  - To KEEP extras: readers.las with extra_dims="all", writers.copc with
    extra_dims="all" and forward="all".

    how to run:
    python las_to_copc_tiled.py \
    --input 01_raw/01_20250325_192511.laz \
    --output ./02_input \
    --site MYSITE
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys
from pathlib import Path

import pdal


# -------------------------------------------------------------------------
# Stage builders
# -------------------------------------------------------------------------
def _make_reader(filename: str, keep_extra_dims: bool) -> dict:
    """readers.las stage. Only request extra dims when we plan to keep them."""
    stage: dict = {"type": "readers.las", "filename": filename}
    if keep_extra_dims:
        # Load all user-defined ExtraBytes declared in the file's VLR.
        stage["extra_dims"] = "all"
    return stage


def _make_copc_writer(filename: str, keep_extra_dims: bool) -> dict:
    """
    writers.copc stage. Never pass an empty extra_dims (some builds reject
    that). When keeping extras, request "all"; when dropping, omit the key
    entirely and rely on the reader not having loaded any extra dims.
    """
    stage: dict = {
        "type": "writers.copc",
        "filename": filename,
        "forward": "all" if keep_extra_dims else "header",
    }
    if keep_extra_dims:
        stage["extra_dims"] = "all"
    return stage


# -------------------------------------------------------------------------
# File discovery
# -------------------------------------------------------------------------
def discover_inputs(input_path: str) -> list[str]:
    """Accept a single file, a directory, or a glob and return a sorted list."""
    p = Path(input_path)
    if p.is_file():
        return [str(p)]
    if p.is_dir():
        files = list(p.glob("*.laz")) + list(p.glob("*.las"))
        return sorted(str(f) for f in files)
    files = glob.glob(input_path)
    if not files:
        raise FileNotFoundError(f"No LAS/LAZ inputs found at: {input_path}")
    return sorted(files)


# -------------------------------------------------------------------------
# Tiling: split each input into N-meter tiles, write each tile to COPC
# -------------------------------------------------------------------------
def tile_and_write(
    in_file: str,
    out_dir: Path,
    site: str,
    tile_size: float,
    keep_extra_dims: bool,
    voxel_size: float | None,
    overwrite: bool,
) -> list[Path]:
    """Read -> (voxel) -> splitter(tile_size) -> per-view COPC write."""

    pipe_stages: list[dict] = [_make_reader(in_file, keep_extra_dims)]

    if voxel_size and voxel_size > 0:
        pipe_stages.append(
            {"type": "filters.voxelcenternearestneighbor", "cell": voxel_size}
        )

    pipe_stages.append(
        {
            "type": "filters.splitter",
            "length": tile_size,
            "origin_x": 0,
            "origin_y": 0,
        }
    )

    pipeline = pdal.Pipeline(json.dumps(pipe_stages))
    pipeline.execute()

    written: list[Path] = []
    for arr in pipeline.arrays:
        if arr.size == 0:
            continue

        xmin = int(math.floor(arr["X"].min() / tile_size) * tile_size)
        ymin = int(math.floor(arr["Y"].min() / tile_size) * tile_size)

        out_name = f"{site}_{xmin}_{ymin}.copc.laz"
        out_path = out_dir / out_name

        if out_path.exists() and not overwrite:
            print(f"  skip (exists): {out_name}")
            continue

        writer_stage = _make_copc_writer(str(out_path), keep_extra_dims)
        write_pipe = pdal.Pipeline(json.dumps([writer_stage]), arrays=[arr])
        write_pipe.execute()
        written.append(out_path)
        print(f"  wrote: {out_name}  ({arr.size:,} pts)")

    return written


# -------------------------------------------------------------------------
# Driver
# -------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(
        description="Convert raw LAS/LAZ to tiled COPC (02_input)."
    )
    ap.add_argument("--input", default="01_raw",
                    help="Input file, directory, or glob (default: 01_raw)")
    ap.add_argument("--output", default="02_input",
                    help="Output directory (default: 02_input)")
    ap.add_argument("--site", required=True,
                    help="Site code prefix for filenames")
    ap.add_argument("--tile-size", type=float, default=250.0,
                    help="Tile edge length in CRS units (default: 250)")
    ap.add_argument("--voxel-size", type=float, default=None,
                    help="Optional voxel thinning cell size in CRS units")
    ap.add_argument("--keep-extra-dims", action="store_true",
                    help="Preserve provider user-defined ExtraBytes")
    ap.add_argument("--merge", action="store_true",
                    help="Merge all inputs before tiling")
    ap.add_argument("--overwrite", action="store_true",
                    help="Overwrite existing output tiles")
    args = ap.parse_args()

    inputs = discover_inputs(args.input)
    if not inputs:
        print(f"No inputs at {args.input}", file=sys.stderr)
        return 1

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"PDAL bindings: {pdal.__version__}")
    print(f"Found {len(inputs)} input file(s).")
    print(f"Site         : {args.site}")
    print(f"Tile size    : {args.tile_size}")
    print(f"Voxel filter : {args.voxel_size if args.voxel_size else 'off'}")
    print(f"Extra dims   : {'kept' if args.keep_extra_dims else 'dropped'}")
    print(f"Output dir   : {out_dir.resolve()}")
    print()

    if args.merge:
        stages: list[dict] = [
            _make_reader(f, args.keep_extra_dims) for f in inputs
        ]
        stages.append({"type": "filters.merge"})
        if args.voxel_size:
            stages.append(
                {"type": "filters.voxelcenternearestneighbor",
                 "cell": args.voxel_size}
            )
        stages.append(
            {"type": "filters.splitter",
             "length": args.tile_size,
             "origin_x": 0,
             "origin_y": 0}
        )

        pipeline = pdal.Pipeline(json.dumps(stages))
        pipeline.execute()

        for arr in pipeline.arrays:
            if arr.size == 0:
                continue
            xmin = int(math.floor(arr["X"].min() / args.tile_size)
                       * args.tile_size)
            ymin = int(math.floor(arr["Y"].min() / args.tile_size)
                       * args.tile_size)
            out_path = out_dir / f"{args.site}_{xmin}_{ymin}.copc.laz"
            if out_path.exists() and not args.overwrite:
                print(f"  skip (exists): {out_path.name}")
                continue
            writer = _make_copc_writer(str(out_path), args.keep_extra_dims)
            pdal.Pipeline(json.dumps([writer]), arrays=[arr]).execute()
            print(f"  wrote: {out_path.name}  ({arr.size:,} pts)")
    else:
        for f in inputs:
            print(f"Processing: {os.path.basename(f)}")
            try:
                tile_and_write(
                    in_file=f,
                    out_dir=out_dir,
                    site=args.site,
                    tile_size=args.tile_size,
                    keep_extra_dims=args.keep_extra_dims,
                    voxel_size=args.voxel_size,
                    overwrite=args.overwrite,
                )
            except Exception as e:
                print(f"  FAILED: {f}\n    {e}", file=sys.stderr)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())