# ClearMap (Stuber Lab HPC fork)

A fork of [ClearMap 1](https://github.com/ChristophKirst/ClearMap) (Renier, Kirst et al.) adapted
for **parallel whole-brain processing on SLURM clusters**. The pipeline runs inside a
Singularity/Apptainer container, and samples are processed as independent batch jobs driven by a
single experiment table.

It is used in the Stuber Lab (University of Washington) for whole-brain c-Fos / FosTRAP mapping of
iDISCO+-cleared mouse brains imaged on a LifeCanvas SmartSPIM.

> **Scope of this fork.** The core algorithms are unchanged from ClearMap 1. What is added here is
> the cluster plumbing: batch job generation, containerisation, dual-channel overlap detection, and
> group-level spatial heatmap statistics. For the current upstream toolbox see
> [ClearMap2](https://github.com/ChristophKirst/ClearMap2) — this fork is *not* based on it.

---

## What's in this fork

| Addition | Where |
|---|---|
| SLURM batch job generation from a CSV experiment table | `ClearMap/Scripts/batch processing/` |
| Singularity/Apptainer definition file | `ClearMap/Scripts/HPC_clearmap.def` |
| Single-sample / debugging templates | `ClearMap/Scripts/single file processing/` |
| Dual-channel overlap detection (KD-tree) | `ClearMap/Analysis/overlap_detection.py` |
| Group-level spatial heatmaps + voxel t-test | `ClearMap/Scripts/Spatial heatmap analysis/` |
| Interactive cell-detection threshold viewer (Python 3, runs locally) | `ClearMap/Scripts/threshold-visualization.py` |
| Annotation support for additional atlases (e.g. Kim ref. v2.7) | `ClearMap/Data/`, `ClearMap/Analysis/Label_YK_*.py` |

## Requirements

The ClearMap 1 code base is **Python 2.7**, so everything except the threshold viewer runs inside
the container rather than in a modern environment:

- Python 2.7 with the pins in `ClearMap/Scripts/requirements.txt`
- [elastix 4.9.0](https://github.com/SuperElastix/elastix) — registration
- [ilastik 1.3.3post3](https://www.ilastik.org/) — optional, for classifier-based segmentation
- A SLURM cluster with Singularity or Apptainer

`ClearMap/Scripts/threshold-visualization.py` is standalone **Python 3** (numpy, matplotlib,
tifffile, pandas, tkinter) and is meant to be run on a workstation, not on the cluster.

## Getting the container

**Option A — pull the prebuilt image:**

```bash
singularity pull clearmap.sif library://kishii1223/repo/clearmap
```

(also browsable at <https://cloud.sylabs.io/library/kishii1223/repo/clearmap>)

**Option B — build from the definition file:**

```bash
sudo singularity build clearmap.sif ClearMap/Scripts/HPC_clearmap.def
```

> **Before building**, edit the `%files` section of `HPC_clearmap.def`: it copies
> `requirements.txt` from a hard-coded path on UW's Klone cluster
> (`/mmfs1/gscratch/nape/common/ClearMap/...`). Point it at your own checkout.

The container clones this repository into `/ClearMap` and puts it on `PYTHONPATH`, so the code
inside the image is pinned to whatever `master` was at build time. To run your own working copy
instead, bind-mount it and prepend it to `PYTHONPATH`:

```bash
singularity exec -B /path/to/ClearMap:/mnt/ClearMap \
  --env PYTHONPATH=/mnt/ClearMap clearmap.sif python your_script.py
```

Registration also needs the ClearMap atlas resources (`clearmap_ressources_mouse_brain`) and a
writable scratch directory; keep both on fast cluster storage.

## Batch processing (the main workflow)

Everything is driven by two files:

**1. `experiment_parameter_tests.csv`** — one row per sample. Columns:

| Column | Meaning |
|---|---|
| `ID` | Sample ID; used for job names and output folders |
| `Condition` | Group label, used by the heatmap statistics |
| `Microscope` | e.g. `SmartSpim2` |
| `BaseDirectory` | Path to the sample's stitched data |
| `variable_file` | Path to the per-sample parameter file |
| `memory`, `cores` | SLURM resource request (e.g. `175G`, `24`) |
| `signal_channel_key`, `bg_channel_key` | Channel folder/file keys, e.g. `Ex_639_Ch2_stitched` |
| `FinalOrientation` | Axis permutation into atlas orientation, e.g. `(1, 3, -2)` |
| `ImageProcessingMethod` | `SpotDetection` or `Ilastik` |
| `xy_res`, `z_res` | Voxel size; `FALSE` to read from metadata |
| `SignalFileRange` | Sub-stack to process, e.g. `{'x': all, 'y': all, 'z': all}` |

**2. `variable_file.xlsx`** — detection/registration parameters per sample.

Then:

```bash
cd "ClearMap/Scripts/batch processing"

# Edit the header of the script: experiment_file, sif_file, PARTITION_NAME,
# ALLOCATION_NAME, EMAIL, TIME
bash batch_submit_jobs.sh
```

This writes one `job_<ID>.sh` per row and submits it with `sbatch`. The other two submitters follow
the same pattern:

| Script | Purpose |
|---|---|
| `batch_submit_jobs.sh` | Full pipeline: resample → register → detect cells → align points |
| `batch_submit_detection_validation_jobs.sh` | Score detection against ground-truth crops (F1) |
| `batch_submit_overlap_detection_jobs.sh` | Two-channel overlap quantification |

To debug a single sample, run a generated script directly (`bash job_<ID>.sh`) or use the templates
in `ClearMap/Scripts/single file processing/`.

## Overlap detection

`ClearMap/Analysis/overlap_detection.py` matches detected cell coordinates between two channels
(e.g. c-Fos and FosTRAP) with a KD-tree nearest-neighbour search within a distance cutoff, then
transforms the matched points into atlas space for region counts. Drive it with
`overlap_detection_for_batch.py` (cluster) or `overlap_analysis_template.py` (single sample).

## Group statistics and heatmaps

```bash
cd "ClearMap/Scripts/Spatial heatmap analysis"
# edit rootpath, experiment_file, control_condition, pcutoff and the SBATCH header
sbatch job_heatmap_stats.sh
```

`heatmap_generation_ttest.py` voxelises aligned points per sample, groups them by the `Condition`
column, and runs a voxel-wise t-test against `control_condition`, writing heatmap volumes to
`rootpath`.

## Repository layout

```
ClearMap/
  Alignment/        resampling, elastix registration
  Analysis/         labelling, statistics, voxelization, overlap_detection
  Data/             atlas annotation tables (ARA2, Kim ref v2.7), flatfield profiles
  IO/               readers/writers for TIF, raw, NRRD, CSV, ...
  ImageProcessing/  spot detection, filters, ilastik interface
  Scripts/          HPC definition file + batch / single-file / heatmap scripts
  Settings.py       paths to elastix and ilastik (see below)
  Parameter.py      default parameter structure
```

### Configuring elastix / ilastik paths

`ClearMap/Settings.py` resolves the elastix and ilastik installations. Set them with environment
variables rather than editing the file:

```bash
export CLEARMAP_ELASTIX_PATH=/elastix-4.9.0-linux
export CLEARMAP_ILASTIK_PATH=/ilastik-1.3.3post3-Linux
```

The container defaults match these paths. Host-specific overrides still live in `Settings.setup()`
for backwards compatibility.

## Known rough edges

- `ClearMap/Analysis/` carries several dated variants (`Label_YK_*`, `Statistics_YK_*`) kept for
  reproducing older analyses. The batch pipeline uses **`Label_YK_24FEB22`** and
  **`Statistics_YK_24FEB22`**; the others are not wired into any script here, and
  `Statistics_YK_2.py` imports a module that is not in the repository.
- Resource requests, partitions and allocations are hard-coded at the top of each `.sh` script and
  must be edited per cluster. The scripts assume SLURM.
- `setup.py` exists for `pip install -e .` (it builds the Cython voxelization extension) but the
  intended deployment is the container, not pip.

## Tutorials

- [ClearMap for whole-brain preprocessing on HPCs](https://youtu.be/6mqsMVrYnPY)
- [Using ClearMap at Bridges-2 via NSF ACCESS](https://youtu.be/VK3FLcL41aY)
- [Globus file transfer between local machines and HPCs](https://youtu.be/4XRtDsjOI4c)
- [Ilastik for cell segmentation](https://youtu.be/AkO2idt92yk)

## Citing

Please cite the original ClearMap papers (Renier et al., *Cell* 2016; Kirst et al., *Cell* 2020) in
addition to this repository.

## Authors and license

- (c) 2016 Christoph Kirst, The Rockefeller University — original ClearMap
- (c) 2024–2026 Kentaro Ishii, University of Washington (<ken1223@uw.edu>) — HPC, batch processing
  and overlap-detection extensions

GPLv3 — see [LICENSE.txt](LICENSE.txt).
