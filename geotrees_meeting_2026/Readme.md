# Creating LAZ to tiled COPC

Convert raw airborne/UAV lidar (`.las` / `.laz`) into [Cloud-Optimized Point Cloud](https://copc.io) (COPC) tiles ready for downstream geotrees workflows. The script reads from `01_raw/`, optionally drops provider-added attributes and thins via a voxel filter, splits the cloud into fixed-size tiles (default **250 m**), and writes them to `02_input/` named `{site}_{Xmin}_{Ymin}.copc.laz`.

---

## 1. Clone the repository

```bash
git clone https://github.com/MAAP-Project/geotrees-demo
cd geotrees-demo/geotrees_meeting_2026
```

You should now see at minimum:

```
geotrees_meeting_2026/
├── environment.yaml
├── las_to_copc_tiled.py
├── README.md
├── 01_raw/         # put your input .las / .laz here
└── 02_input/       # tiled COPC outputs land here
```

If `01_raw/` and `02_input/` don't exist yet:

```bash
mkdir -p 01_raw 02_input
```
or clone into the repository with your raw data.

---

## 2. Create the conda environment

The pinned environment uses **conda-forge** for PDAL + its Python bindings (this combination cannot be installed reliably with `pip` alone — PDAL needs its C++ library, and conda-forge ships the matching pair).

```bash
# Create the env from the YAML (one-time setup)
conda env create -f environment.yaml

# Activate it
conda activate copc

# Sanity check
pdal --version
python -c "import pdal; print('python-pdal', pdal.__version__)"
```

If you ever change `environment.yaml`, update an existing env with:

```bash
conda env update -f environment.yaml --prune
```

To remove the env entirely:

```bash
conda env remove -n copc
```

---

## 3. Put input data in `01_raw/`

Drop any `.las` or `.laz` files into `01_raw/`. The script accepts:

- a single file (`--input path/to/file.laz`),
- a directory (`--input 01_raw`, the default),
- or a glob (`--input "01_raw/*_2025*.laz"`).

> Inputs should be in a **projected CRS in meters** (UTM, state plane, etc.) so that the 250 m tile grid and `{Xmin, Ymin}` filenames are meaningful. If your file is in lat/lon degrees, reproject it first with PDAL (see "Common gotchas" below).

---

## 4. Run the script

### 4a. Minimum invocation

Process every `.las`/`.laz` in `01_raw/`, write 250 m COPC tiles to `02_input/`:

```bash
python las_to_copc_tiled.py --site MYSITE
```

### 4b. Single file

```bash
python las_to_copc_tiled.py \
    --input 01_raw/01_20250325_192511.laz \
    --output ./02_input \
    --site MYSITE
```

### 4c. Thin the cloud (voxel filter)

Keep one point per voxel of the given size (CRS units, typically meters). Good for reducing dense scans before downstream processing.

```bash
# 1 m voxel — roughly one point per cubic meter
python las_to_copc_tiled.py --site MYSITE --voxel-size 1.0

# 0.25 m voxel — finer thinning
python las_to_copc_tiled.py --site MYSITE --voxel-size 0.25
```

### 4d. Drop vs. keep provider ExtraBytes

By default the script **drops** user-defined ExtraBytes (e.g., provider post-processing attributes like return ratios, classification confidence, scan-angle-rank variants) to reduce file size.

To preserve them:

```bash
python las_to_copc_tiled.py --site MYSITE --keep-extra-dims
```

### 4e. Custom tile size

```bash
# 500 m tiles instead of 250 m
python las_to_copc_tiled.py --site MYSITE --tile-size 500
```

### 4f. Merge multiple inputs before tiling

Useful when your raw files are arbitrary swaths and you want clean 250 m tiles spanning their union. **Loads everything into memory** — use with care on large collections.

```bash
python las_to_copc_tiled.py --site MYSITE --merge
```

### 4g. Re-run / overwrite existing tiles

By default the script skips outputs that already exist (handy for resuming a long run). To force regeneration:

```bash
python las_to_copc_tiled.py --site MYSITE --overwrite
```

### 4h. A "kitchen sink" example

```bash
python las_to_copc_tiled.py \
    --input "01_raw/*.laz" \
    --output 02_input \
    --site NEON_HARV \
    --tile-size 250 \
    --voxel-size 1.0 \
    --overwrite
```

---

## 5. Output

You'll get files like:

```
02_input/
├── MYSITE_325000_4567250.copc.laz
├── MYSITE_325000_4567500.copc.laz
├── MYSITE_325250_4567250.copc.laz
└── ...
```

The two numbers are the tile's **Xmin** and **Ymin** in the input CRS, floored to the tile grid (so a 250 m tile starting at `X = 325137.4` is named with `325000`).

Inspect one with:

```bash
pdal info 02_input/MYSITE_325000_4567250.copc.laz --summary
```

---

## 6. All CLI flags at a glance

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--input` | path / dir / glob | `01_raw` | Where to read inputs from |
| `--output` | dir | `02_input` | Where to write COPC tiles |
| `--site` | str | **required** | Filename prefix (e.g. `NEON_HARV`) |
| `--tile-size` | float | `250.0` | Tile edge length, CRS units |
| `--voxel-size` | float | _off_ | If set, thin to 1 pt per voxel of this size |
| `--keep-extra-dims` | flag | off | Preserve provider user-defined ExtraBytes |
| `--merge` | flag | off | Merge all inputs before tiling |
| `--overwrite` | flag | off | Overwrite existing output tiles |

---

## 7. Common gotchas

**"No inputs at 01_raw"** — Check that your file extensions are lowercase (`.laz` / `.las`). Adjust the path or use `--input` to point elsewhere.

**Tiles come out with weird names like `MYSITE_0_0.copc.laz`** — Your input is probably in geographic coordinates (degrees), not projected meters. Reproject first:

```bash
pdal translate input.laz reprojected.laz reprojection \
    --filters.reprojection.out_srs=EPSG:32616     # pick your UTM zone
```

Then run the script on `reprojected.laz`.

**Out-of-memory on `--merge`** — Drop `--merge` and process per-file (the default). Each input still lands in `02_input/` with the same naming convention; tiles from neighboring inputs that share a grid cell will end up as separate files you can post-merge per cell if needed.

**`writers.copc: Unexpected argument 'extra_dims'` or `Missing value for argument 'extra_dims'`** — These come from older PDAL builds. The current script avoids them by handling ExtraBytes at the reader level. If you still see issues, upgrade PDAL:

```bash
conda update -n coguide-copc -c conda-forge pdal python-pdal
```

**Tile-grid origin doesn't align with your AOI** — The script snaps tiles to the CRS origin (`0, 0`). If you'd rather have tiles snap to a specific southwest corner, edit the `origin_x` / `origin_y` in `filters.splitter` inside `las_to_copc_tiled.py`.

---

## 8. Quick reference: full workflow from scratch

```bash
# 1. Get the code
git clone <your-repo-url> geotrees_meeting_2026
cd geotrees_meeting_2026

# 2. Build the env (one time)
conda env create -f environment.yaml
conda activate coguide-copc

# 3. Drop your raw lidar into 01_raw/
cp /path/to/lidar/*.laz 01_raw/

# 4. Convert
python las_to_copc_tiled.py --site MYSITE --voxel-size 1.0

# 5. Verify
ls 02_input/
pdal info 02_input/MYSITE_*.copc.laz --summary | head -20
```

---

## Reference:

The conversion script is adapted from the MAAP-Project `geotrees-demo` reference implementation:
<https://github.com/MAAP-Project/geotrees-demo/blob/main/convert_las_to_copc.py>