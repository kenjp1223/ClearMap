# -*- coding: utf-8 -*-
"""
Template to run the processing pipeline
"""
import time
import pandas as pd

start = time.time()

print("Start analysis")

#load the parameters:
execfile('.../parameter_file_template.py') #user specific

#Segmentation testing
################################
#crop images to create test/train classifier
generate_random_crops.main(**CropGeneratingParameter)

#run cell detection on the generated dataset
#run a for loop though all crops
rootpath = os.path.join(CropGeneratingParameter['output_folder'],'train')
for fname in [f for f in os.listdir(rootpath) if '.tif' in f]:
   # update parameters for each crop
   CropGeneratingParameter['source'] = os.path.join(rootpath, fname)
   CropGeneratingParameter['sink'] = ( os.path.join(rootpath, fname.replace('.tif','_Spot_cells-allpoints.npy')),\
                                       os.path.join(rootpath, fname.replace('.tif','_Spot_intensities-allpoints.npy')))
   # cell detection                                       
   detectCells(**CropGeneratingParameter);

   #Filtering of the detected peaks:
   #################################
   #Loading the results:
   points, intensities = io.readPoints(CropGeneratingParameter["sink"]);

   #Thresholding: the threshold parameter is either intensity or size in voxel, depending on the chosen "row"
   #row = (0,0) : peak intensity from the raw data
   #row = (1,1) : peak intensity from the DoG filtered data
   #row = (2,2) : peak intensity from the background subtracted data
   #row = (3,3) : voxel size from the watershed
   FilteredCellsFile = (   os.path.join(rootpath, fname.replace('.tif','_Spot_cells.npy')),\
                           os.path.join(rootpath, fname.replace('.tif','_Spot_intensities.npy')));

   points, intensities = thresholdPoints(points, intensities, threshold = (50,5000), row = (3,3));
   io.writePoints(FilteredCellsFile, (points, intensities));


   ## Check Cell detection 
   #######################
   import ClearMap.Visualization.Plot as plt;
   pointSource= FilteredCellsFile[0];
   data = plt.overlayPoints(SignalFile, pointSource, pointColor = None, **SignalFileRange);
   io.writeData(os.path.join(rootpath, fname.replace('.tif','_Spot_cells_check.tif'), data));

#####################

# Fin
end = time.time()
print("The entire process ended in ",end - start)
