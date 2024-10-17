#!/bin/bash
#SBATCH --job-name=heatmap_stats
#SBATCH --output=processing_job_heatmap_stats.out
#SBATCH --error=slurm-%j-processing_job_heatmap_stats.err
#SBATCH -A ACCOUNT
#SBATCH -p RM
#SBATCH -n 128
#SBATCH --time=1:00:00
#SBATCH --mail-type=end          # send email when job ends
#SBATCH --mail-user=email@uw.edu

# Set environment variables
export rootpath="ANYPATH" # an output directory will be created here
export experiment_file="experiment_parameter_tests.csv"
export control_condition="CONTROL"
export pcutoff=0.05

# Run your Python script
# Use apptainer or singularity depending on the cluster environment
module purge
#module load apptainer
singularity exec "PATH_TO_.sif" python heatmap_generation_ttest.py


