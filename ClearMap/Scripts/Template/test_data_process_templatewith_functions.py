# -*- coding: utf-8 -*-
"""
Template to run the processing pipeline
"""
import time
import pandas as pd

start = time.time()

print("Start analysis")


# read the experiment file
# specify the path as variable experiment_file
experiment_file = os.environ.get('experiment_file')
variable_file = os.environ.get('variable_file')

# read the ID index that is used to extract the subject to analyze
id_index = os.environ.get('id_index')
id_index = int(id_index)

#load the parameters:
execfile('.../parameter_file_template_with_function.py') #user specific

# Change here to determine whether you want to crop and/or detection
crop_flag = CropGeneratingParameter['crop_flag']
detection_flag = CropGeneratingParameter['detection_flag']

################################
#crop images to create test/train classifier
if crop_flag:
   #print(CropGeneratingParameter['fkey'])
   if os.path.exists(CropGeneratingParameter['output_folder']):
      shutil.rmtree(CropGeneratingParameter['output_folder'], ignore_errors=True)
   generate_random_crops.main(**CropGeneratingParameter)

#run cell detection on the generated dataset
#run a for loop though all crops
if detection_flag:
   #run cell detection on the generated dataset
   #run a for loop though all crops
   for filetype in ['train','test']:
      rootpath = os.path.join(CropGeneratingParameter['output_folder'],filetype)
      for fname in [f for f in os.listdir(rootpath) if '.tif' in f and 'check' not in f]:
         # update parameters for each crop
         CropImageProcessingParameter['source'] = os.path.join(rootpath, fname)
         CropImageProcessingParameter['sink'] = ( os.path.join(rootpath, fname.replace('.tif','_Spot_cells-allpoints.npy')),\
                                             os.path.join(rootpath, fname.replace('.tif','_Spot_intensities-allpoints.npy')))
         # cell detection                                       
         detectCells(**CropImageProcessingParameter);

         #Filtering of the detected peaks:
         #################################
         #Loading the results:
         points, intensities = io.readPoints(CropImageProcessingParameter["sink"]);

         #Thresholding: the threshold parameter is either intensity or size in voxel, depending on the chosen "row"
         #row = (0,0) : peak intensity from the raw data
         #row = (1,1) : peak intensity from the DoG filtered data
         #row = (2,2) : peak intensity from the background subtracted data
         #row = (3,3) : voxel size from the watershed
         FilteredCellsFile = (   os.path.join(rootpath, fname.replace('.tif','_Spot_cells.npy')),\
                                 os.path.join(rootpath, fname.replace('.tif','_Spot_intensities.npy')));

         for threshold,row in zip(thresholdParameter['threshold'],thresholdParameter['row']):
            points, intensities = thresholdPoints(points, intensities, threshold = threshold, row = row);
         io.writePoints(FilteredCellsFile, (points, intensities));


         ## Check Cell detection 
         #######################
         import ClearMap.Visualization.Plot as plt;
         pointSource= FilteredCellsFile[0];
         data = plt.overlayPoints(CropImageProcessingParameter['source'], pointSource, pointColor = None, **SignalFileRange);
         io.writeData(os.path.join(rootpath, fname.replace('.tif','_Spot_cells_check.tif')), data);

#####################

# Fin
end = time.time()
print("The entire process ended in ",end - start)
