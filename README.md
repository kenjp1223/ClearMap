ClearMap
========

This is a fork of ClearMap.
Updates on some of the source code plus some additional files to allow annotations on new brain atlas files.
Updates on some of the source code so it can run on the cluster.

2/18/2025
========
Main scripts used on the HPCs are found in the script folder.
The environment file (.sif) file is found in this repo, or you can construct using a def file.
https://cloud.sylabs.io/library/kishii1223/repo/clearmap


4/16/2024
========
Added features for overlap analysis.
The analysis is meant to be used for c-Fos and FosTRAP dual labeling


4/20/2024
========
Added a bash script that will take in two files:
experiment_parameter_tests.csv: The meta data of the experiment. The bash script will go through all the rows in this file and process each data.
variable_file.xlsx: The meta data of the processing. The variables for each process step should be stated in this file.
submit_jobs.sh: Takes in the experiment_parameter_tests.csv and creates bash script for individual rows and runs it.

Major Updates in This Fork
=========================

1. Parallel and Batch Processing for HPCs
-----------------------------------------
- **Batch Scripts for HPC:**
  - Added bash scripts in `ClearMap/Scripts/batch processing/` (e.g., `batch_submit_jobs.sh`, `batch_submit_detection_validation_jobs.sh`, `batch_submit_overlap_detection_jobs.sh`) to automate job submission to SLURM-based HPC clusters.
  - Scripts read experiment metadata from CSV files and generate per-sample job scripts, enabling large-scale, parallelized processing.
  - Resource allocation (memory, cores) and environment variables are set per job; jobs are submitted using `sbatch`.
  - Supports both segmentation validation and overlap detection in batch mode.
- **Singularity/Apptainer Integration:**
  - Scripts are designed to run ClearMap inside a container (using `.sif` images), ensuring reproducibility and ease of deployment on clusters.
  - A definition file (`HPC_clearmap.def`) is provided to build the container with all dependencies.
- **Parameterization:**
  - Processing and detection parameters are externalized in CSV/XLSX files (`experiment_parameter_tests.csv`, `variable_file.xlsx`), making the pipeline flexible and easy to adapt to new experiments.

2. Single-File and Template Processing
--------------------------------------
- Scripts in `ClearMap/Scripts/single file processing/` (e.g., `process_template.py`, `detection_validation.py`, `overlap_analysis_template.py`) provide templates for running the ClearMap pipeline on individual files, useful for debugging or small-scale runs.

3. Overlap Detection
--------------------
- **New Overlap Detection Pipeline:**
  - Added scripts and functions for overlap analysis between two channels (e.g., c-Fos and FosTRAP dual labeling).
  - `ClearMap/Analysis/overlap_detection.py` provides efficient functions to find spatial overlaps between detected cell coordinates using KD-trees.
  - Batch and single-file scripts automate the process of overlap detection, transformation, and quantification.

4. Spatial Heatmap and Statistical Analysis
-------------------------------------------
- **Spatial Heatmap Generation:**
  - Scripts in `ClearMap/Scripts/Spatial heatmap analysis/` (e.g., `heatmap_generation_ttest.py`, `job_heatmap_stats.sh`) allow for the generation of spatial heatmaps and statistical comparison (e.g., t-tests) across experimental groups.

5. Other Improvements
---------------------
- **Parallelization in Core Processing:**
  - Many parameter files now include options for setting the number of parallel processes for resampling, stack processing, and cell detection, making use of available HPC resources.
- **Documentation and Templates:**
  - Example parameter files and templates are provided to help users adapt the pipeline to their own data and cluster environment.

How to Use
==========
- **Batch Processing:**
  1. Prepare your experiment metadata (`experiment_parameter_tests.csv`) and variable file (`variable_file.xlsx`).
  2. Use the provided batch submission scripts to generate and submit jobs to your cluster.
  3. Monitor outputs and logs for each sample/job.
- **Single File Processing:**
  - Use the templates in `single file processing/` for step-by-step or debugging runs.
- **Overlap Detection:**
  - Use the overlap detection scripts to quantify dual-labeled cells or other spatial overlaps.
- **Containerized Execution:**
  - Build the container using `HPC_clearmap.def` or use the provided `.sif` file for reproducible runs.

Copyright
---------
    (c) 2016 Christoph Kirst
    The Rockefeller University, 
    ckirst@rockefeller.edu

License
-------
    GPLv3, see LICENSE.txt for details.
