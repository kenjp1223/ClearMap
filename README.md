ClearMap
========

This is a fork of ClearMap.
Updates on some of the source code plus some additional files to allow annotations on new brain atlas files.
Updates on some of the source code so it can run on the cluster.



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

Singularity containers
========
The environment file (.sif) file can be downloaded from the following repository.
https://cloud.sylabs.io/library/kishii1223/repo/clearmap
Alternatively, you can use the def file located in the scripts folder

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

Execution Instructions for Batch Scripts
========================================

To run the ClearMap batch processing pipeline on an HPC, follow these steps:

1. **Navigate to the Scripts Directory**
   ```bash
   cd /path/to/ClearMap/Scripts/batch processing
   ```

2. **Edit the Batch Submission Script(s)**
   - Open the relevant batch submission script (e.g., `batch_submit_jobs.sh`, `batch_submit_detection_validation_jobs.sh`, or `batch_submit_overlap_detection_jobs.sh`) in a text editor.
   - Update the following variables at the top of the script to match your environment:
     - `experiment_file` (path to your experiment CSV file)
     - `sif_file` (path to your Singularity/Apptainer .sif image)
     - `PARTITION_NAME` (your cluster's partition/queue name)
     - `ALLOCATION_NAME` (your allocation/project name)
     - `EMAIL` (your email for job notifications)
     - `TIME` (walltime for each job, if needed)

3. **Edit Parameter Files as Needed**
   - Make sure your `experiment_parameter_tests.csv` and `variable_file.xlsx` (or other parameter files) are correctly set up for your experiment.

4. **Run the Batch Submission Script**
   - Execute the batch submission script to generate and submit job scripts:
   ```bash
   bash batch_submit_jobs.sh
   # or for overlap detection:
   bash batch_submit_overlap_detection_jobs.sh
   # or for detection validation:
   bash batch_submit_detection_validation_jobs.sh
   ```
   - This will create individual job scripts (e.g., `job_*.sh`) and submit them to the cluster using `sbatch`.

5. **(Optional) Manually Run a Generated Job Script**
   - If you want to run a generated job script manually (for debugging or single runs):
   ```bash
   bash job_SAMPLEID.sh
   ```
   - Replace `job_SAMPLEID.sh` with the actual script name generated for your sample.


**Note:**
- Always double-check the paths and resource settings in your scripts before submitting jobs.
- The scripts are designed for SLURM clusters; for other schedulers, you may need to adapt the submission commands.

Other resources for the usage of ClearMap on HPCs
========================================
- Overview of using ClearMap for wholebrain data preprocessing on HPCs
https://youtu.be/6mqsMVrYnPY

- Using ClearMap at Bridges-2 through NSF ACCESS program
https://youtu.be/VK3FLcL41aY

- Using Globus for file transfer between local and HPCs
https://youtu.be/4XRtDsjOI4c

- Using Ilastik for cell segmentation
https://youtu.be/AkO2idt92yk

Copyright
---------
    (c) 2016 Christoph Kirst
    The Rockefeller University, 
    ckirst@rockefeller.edu


    (c) 2024 Kentaro Ishii
    University of Washington
    ken1223@uw.edu
    Significant modifications and extensions for HPC and batch processing.
License
-------
    GPLv3, see LICENSE.txt for details.
