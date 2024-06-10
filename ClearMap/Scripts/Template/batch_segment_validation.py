# -*- coding: utf-8 -*-
"""
Template to run the processing pipeline

This script is a template for running a processing pipeline. It performs various steps including reading experiment files,
loading parameters, generating random crops for segmentation evaluation, applying cell detection on the crops, filtering
the detected peaks, and visualizing the results. The script also measures the time taken for each step and the entire process.

Author: Kentaro Ishii
Date: 5/29/2024

Usage:
- Set the path to the experiment file and variable file using the environment variables 'experiment_file' and 'variable_file'.
- Set the index of the subject to analyze using the environment variable 'id_index'.
- Update the parameter file 'parameter_file_for_Segmentation_Validation_template_with_function.py' with the required parameters.
- The images generated in "generate_random_crops.main" will be saved in a folder named signal_key + 'crops'. There will be a "train" and "test" file in the folder.
- If you generated your own cropped image files, save them in a folder named signal_key + 'crops'.
Note: This script assumes the existence of other modules and functions such as 'generate_random_crops', 'detectCells',
'thresholdPoints', 'io', and 'plt' from the ClearMap package.

"""

import time
import pandas as pd
import os

start = time.time()

print("Start analysis")

# read the experiment file
# specify the path as variable experiment_file
experiment_file = os.environ.get('experiment_file')
variable_file = os.environ.get('variable_file')

# read the ID index that is used to extract the subject to analyze
id_index = os.environ.get('id_index')
id_index = int(id_index)

print("Processing subject index ", id_index, "in experiment file", experiment_file)

#load the parameters:
execfile('batch_parameter_file.py') #user specific

#Generate random crops for segmentation evaluation
crop_flag = CropGeneratingParameter['crop_flag']
detection_flag = CropGeneratingParameter['detection_flag']
del CropGeneratingParameter['crop_flag'],CropGeneratingParameter['detection_flag']

if crop_flag:
   generate_random_crops.main(**CropGeneratingParameter)


# Run through the generated crops and apply cell detection.
if detection_flag:
   for ftype in ['train','test']:
      BaseDirectory = os.path.join(CropGeneratingParameter['output_folder'],ftype)
      for SignalFile in os.listdir(BaseDirectory):
         if not '.tif' in SignalFile or '_check.tif' in SignalFile:
            continue
         fname = SignalFile.replace('.tif','')
         # Update the imaging parameters
         ImageProcessingParameter["source"] = os.path.join(BaseDirectory, SignalFile)
         ImageProcessingParameter["sink"] = (os.path.join(BaseDirectory, fname + '_Spot_cells-allpoints.npy'),  os.path.join(BaseDirectory,  fname + '_Spot_intensities-allpoints.npy'))

         detectCells(**ImageProcessingParameter);

         #Filtering of the detected peaks:
         #################################
         #Loading the results:
         points, intensities = io.readPoints(ImageProcessingParameter["sink"]);

         #Thresholding: the threshold parameter is either intensity or size in voxel, depending on the chosen "row"
         FilteredCellsFile = (os.path.join(BaseDirectory, fname + '_Spot_cells.npy'), os.path.join(BaseDirectory,  fname + '_Spot_intensities.npy'));

         for threshold,row in zip(thresholdParameter['threshold'],thresholdParameter['row']):
            points, intensities = thresholdPoints(points, intensities, threshold = threshold, row = row);
         io.writePoints(FilteredCellsFile, (points, intensities));


         ## Check Cell detection (For the testing phase only, remove when running on the full size dataset)
         #######################
         import ClearMap.Visualization.Plot as plt;
         pointSource= os.path.join(BaseDirectory, FilteredCellsFile[0]);
         data = plt.overlayPoints(ImageProcessingParameter["source"], pointSource, pointColor = None, **SignalFileRange);
         io.writeData(os.path.join(BaseDirectory, fname + '_Spot_cells_check.tif'), data);

         ## Check Cell detection (For the testing phase only, remove when running on the full size dataset)
         #######################
         pointSource= os.path.join(BaseDirectory, ImageProcessingParameter["sink"][0]);
         data = plt.overlayPoints(ImageProcessingParameter["source"], pointSource, pointColor = None, **SignalFileRange);
         io.writeData(os.path.join(BaseDirectory, fname + '_Spot_unfilteredcells_check.tif'), data);
      #####################

         # Fin
         end = time.time()
         print("One file process ended in ",end - start)

#####################

# Fin
end = time.time()
print("The entire process ended in ",end - start)
