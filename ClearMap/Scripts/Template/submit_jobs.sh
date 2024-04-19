#!/bin/bash
# change the following depending on your file
experiment_file=/PATH/TO/EXPERIMENT_FILE #.csv file
sif_file=/PATH/TO/SIFFILE # .sif file

# Find column indices for 'ID' and 'variable_file'
file_name_index=$(awk -F',' 'NR==1{for(i=1;i<=NF;i++) if($i=="ID") print i}' "$experiment_file")
variable_file_index=$(awk -F',' 'NR==1{for(i=1;i<=NF;i++) if($i=="variable_file") print i}' "$experiment_file")

# Read subject information from CSV file and submit Slurm jobs
declare -i id_index=0
while IFS=, read -r line; do
    # skip header
    if [[ ! $first_line ]]; then
        first_line=1
        continue
    fi
    # process

    # Skip empty lines
    if [[ -z "$line" || "$line" == "NaN" ]]; then
        continue
    fi

    # Extract column index for 'ID' header using awk
    file_name=$(echo "$line" | awk -F ',' -v idx="$file_name_index" '{print $idx}')
    variable_file=$(echo "$line" | awk -F ',' -v idx="$variable_file_index" '{print $idx}')

    # echo "$line"
    # Output extracted values for testing (replace with your logic)
    echo "file_name: $file_name"
    echo "Variable File: $variable_file"
    

    # Define Slurm job name
    job_name="processing_job_${file_name}"
    
    # Define Slurm job script name
    job_script="job_${file_name}.sh"
    
    # Write Slurm job script
    cat > "$job_script" << EOF

#!/bin/bash
#SBATCH --job-name=$job_name
#SBATCH --output=$job_name.out
#SBATCH --error=$job_name.err
#SBATCH -A ALLOCATION_NAME
#SBATCH -p PARTITION_NAME
#SBATCH --nodes=1
#SBATCH --cpus-per-task=20
#SBATCH --mem=50G
#SBATCH --time=12:00:00

# Set environment variables
export id_index="$id_index"
export file_name="$file_name"
export variable_file="$variable_file"
export experiment_file="$experiment_file"

# Run your Python script
module load apptainer
apptainer exec "$sif_file" python process_template_with_functions.py

EOF
    id_index=$id_index+1
    # Submit Slurm job
    sbatch "$job_script"

done < "$experiment_file"
