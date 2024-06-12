#!/bin/bash
#SBATCH --time=48:00:00                  # Max run time
#SBATCH --job-name=clearmap_template           # Job name
#SBATCH -p EM
#SBATCH -n 24
#SBATCH -e slurm-%j.err                  # Error file for this job.
#SBATCH -A PROJECTNAME  # Project allocation account name (REQUIRED)
#SBATCH --mail-type=begin        # send email when job begins
#SBATCH --mail-type=end          # send email when job ends
#SBATCH --mail-user=XXX@YYY
#SBATCH -o clearmap_template.out

module purge
singularity exec .../clearmap.sif python process_template.py
singularity exec .../clearmap.sif python detecion_validation.py
