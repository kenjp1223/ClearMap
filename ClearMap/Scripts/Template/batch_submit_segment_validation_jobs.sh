#!/bin/bash
# change the following depending on your file
experiment_file=/PATH/TO/EXPERIMENT_FILE #.csv file
sif_file=/PATH/TO/SIFFILE # .sif file
TIME="1:00:00"
PARTITION_NAME=PARTITION_NAME
ALLOCATION_NAME=ALLOCATION_NAME

# Find column indices for 'ID' and 'variable_file'
file_name_index=$(awk -F',' 'NR==1{for(i=1;i<=NF;i++) if($i=="ID") print i}' "$experiment_file")
memory_index=$(awk -F',' 'NR==1{for(i=1;i<=NF;i++) if($i=="memory") print i}' "$experiment_file")
core_index=$(awk -F',' 'NR==1{for(i=1;i<=NF;i++) if($i=="cores") print i}' "$experiment_file")
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
    memory=$(echo "$line" | awk -F ',' -v idx="$memory_index" '{print $idx}')
    cores=$(echo "$line" | awk -F ',' -v idx="$core_index" '{print $idx}')

    # echo "$line"
    # Output extracted values for testing (replace with your logic)
    echo "file_name: $file_name"
    echo "Variable File: $variable_file"
    echo "Memory: $memory"
    echo "Cores: $cores"    

    # Remove the 'G' suffix
    memory_without_suffix="${memory%"G"}"

    # Convert to megabytes
    memory_in_mb=$(( memory_without_suffix * 1024 ))


    # Define Slurm job name
    job_name="processing_job_seg_val_${file_name}"
    
    # Define Slurm job script name
    job_script="job_seg_val_${file_name}.sh"
    
    # Write Slurm job script
    cat > "$job_script" << EOF
#!/bin/bash
#SBATCH --job-name=$job_name
#SBATCH --output=$job_name.out
#SBATCH --error=slurm-%j-$job_name.err
#SBATCH -A $ALLOCATION_NAME
#SBATCH -p $PARTITION_NAME
#SBATCH -n $cores
#SBATCH --mem=$memory
#SBATCH --time=$TIME

# Set environment variables
export id_index="$id_index"
export file_name="$file_name"
export variable_file="$variable_file"
export experiment_file="$experiment_file"

# Run your Python script
# Use apptainer or singularity depending on the cluster environment
module purge
#module load apptainer
singularity exec "$sif_file" python batch_segment_validation.py # Use this for Segmentation validation


EOF

    # Define ilastik parameter file name
    # This is necessary to allow more extensive parallel processing
    ilastik_script="$HOME/.ilastikrc"

    cat > "$ilastik_script" << EOF
[lazyflow]
total_ram_mb=$memory_in_mb
threads=$cores

EOF

    id_index=$id_index+1
    # Submit Slurm job
    sbatch "$job_script"

done < "$experiment_file"
