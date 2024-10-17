#!/bin/bash
#SBATCH --job-name=heatmap_stats
#SBATCH --output=processing_job_heatmap_stats.out
#SBATCH --error=slurm-%j-processing_job_heatmap_stats.err
#SBATCH -A oth240001p
#SBATCH -p RM
#SBATCH -n 128
#SBATCH --time=1:00:00
#SBATCH --mail-type=end          # send email when job ends
#SBATCH --mail-user=ken1223@uw.edu

# Set environment variables
export rootpath="/ocean/projects/oth240001p/adhaka/Scripts_ken" # an output directory will be created here
export experiment_file="experiment_parameter_tests3.csv"
export control_condition="Vehicle"
export pcutoff=0.05

# Run your Python script
# Use apptainer or singularity depending on the cluster environment
module purge
#module load apptainer
#singularity exec "/ocean/projects/oth240001p/shared/clearmap_latest.sif" python batch_segment_validation.py # Use this for Segmentation validation
singularity exec "/ocean/projects/oth240001p/shared/clearmap_latest.sif" python heatmap_generation_ttest.py


