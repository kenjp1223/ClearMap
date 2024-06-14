# -*- coding: utf-8 -*-
"""
Template to run the processing pipeline
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

#resampling operations:
#######################
#resampling for the correction of stage movements during the acquisition between channels:
resampleData(**CorrectionResamplingParameterSignal);
resampleData(**CorrectionResamplingParameterAutoFluo);

#Downsampling for alignment to the Atlas:
resampleData(**RegistrationResamplingParameter);

#Alignment operations:
######################
#correction between channels:
resultDirectory  = alignData(**CorrectionAlignmentParameter);

#alignment to the Atlas:
resultDirectory  = alignData(**RegistrationAlignmentParameter);
transformData(**TransformParameter);
#transformData(**ContourTransformParameter);

# Checking alignment quality
binary_f1_output = F1Scores_NoContours(RegistrationResamplingParameter["sink"], TransformParameter['sink'] ,os.path.join(BaseDirectory, 'overlap_f1score.npy'))
plotF1(binary_f1_output,os.path.join(BaseDirectory, 'overlap_f1score.png'))

#Cell detection:
################
detectCells(**ImageProcessingParameter);

#Transform brain to atlas:
transformData(**TransformParameter);


#Filtering of the detected peaks:
#################################
#Loading the results:
points, intensities = io.readPoints(ImageProcessingParameter["sink"]);

#Thresholding: the threshold parameter is either intensity or size in voxel, depending on the chosen "row"
###SpotDetection
#row = (0,0) : peak intensity from the raw data
#row = (1,1) : peak intensity from the DoG filtered data
#row = (2,2) : peak intensity from the background subtracted data
#row = (3,3) : voxel size from the watershed
###Ilastik
#row = (0,0) : peak intensity from the raw data
#row = (1,1) : voxel size after segmentation
for threshold,row in zip(thresholdParameter['threshold'],thresholdParameter['row']):
   points, intensities = thresholdPoints(points, intensities, threshold = threshold, row = row);
io.writePoints(FilteredCellsFile, (points, intensities));

# Transform point coordinates
#############################
points = io.readPoints(CorrectionResamplingPointsParameter["pointSource"]);
points = resamplePoints(**CorrectionResamplingPointsParameter);
points = transformPoints(points, transformDirectory = CorrectionAlignmentParameter["resultDirectory"], indices = False, resultDirectory = None);
CorrectionResamplingPointsInverseParameter["pointSource"] = points;
points = resamplePointsInverse(**CorrectionResamplingPointsInverseParameter);
RegistrationResamplingPointParameter["pointSource"] = points;
points = resamplePoints(**RegistrationResamplingPointParameter);
points = transformPoints(points, transformDirectory = RegistrationAlignmentParameter["resultDirectory"], indices = False, resultDirectory = None);
io.writePoints(TransformedCellsFile, points);

# Heat map generation
#####################
points = io.readPoints(TransformedCellsFile)
intensities = io.readPoints(FilteredCellsFile[1])

#Without weigths:
vox = voxelize(points, AtlasFile, **voxelizeParameter);
if not isinstance(vox, basestring):
   io.writeData(os.path.join(BaseDirectory, signal_channel_key + '_cells_heatmap.tif'), vox.astype('int32'));

#With weigths from the intensity file (here raw intensity):
voxelizeParameter["weights"] = intensities[:,0].astype(float);
vox = voxelize(points, AtlasFile, **voxelizeParameter);
if not isinstance(vox, basestring):
   io.writeData(os.path.join(BaseDirectory, signal_channel_key + '_cells_heatmap_weighted.tif'), vox.astype('int32'));

#Table generation:
##################
#With integrated weigths from the intensity file (here raw intensity):
#ids, counts = countPointsInRegions(points, labeledImage = AnnotationFile, intensities = intensities, intensityRow = 0);
#table = numpy.zeros(ids.shape, dtype=[('id','int64'),('counts','f8'),('name', 'a256')])
#table["id"] = ids;
#table["counts"] = counts;
#table["name"] = labelToName(ids);
#io.writeTable(os.path.join(BaseDirectory, signal_channel_key + '_Annotated_counts_intensities.csv'), table);

#Without weigths (pure cell number):
ids, counts = countPointsInRegions(points, labeledImage = AnnotationFile, intensities = None, collapse = None);
table = numpy.zeros(ids.shape, dtype=[('id','int64'),('counts','f8'),('name', 'a256')])
table["id"] = ids;
table["counts"] = counts;
table["name"] = labelToName(ids);
io.writeTable(os.path.join(BaseDirectory, signal_channel_key + '_Annotated_counts.csv'), table);

#####################

#clean_table(os.path.join(BaseDirectory, signal_channel_key + '_Annotated_counts_intensities.csv'),AtlasInfoFile)
clean_table(os.path.join(BaseDirectory, signal_channel_key + '_Annotated_counts.csv'),AtlasInfoFile)



#####################

# Fin
end = time.time()
print("The entire process ended in ",end - start)

