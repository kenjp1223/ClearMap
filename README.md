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

Copyright
---------
    (c) 2016 Christoph Kirst
    The Rockefeller University, 
    ckirst@rockefeller.edu

License
-------
    GPLv3, see LICENSE.txt for details.
