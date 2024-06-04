# -*- coding: utf-8 -*-
"""
Example script to set up the parameters for the image processing pipeline
"""

######################### Import modules

import os, numpy, math
import sys
import pandas as pd

import tempfile
tempfile.gettempdir()
import ClearMap.Settings as settings
import ClearMap.IO as io
from ClearMap.Alignment.Resampling import resampleData;
from ClearMap.Alignment.Elastix import alignData, transformPoints
from ClearMap.ImageProcessing.CellDetection import detectCells
from ClearMap.Alignment.F1_Score import LoadingData, F1Scores_WithContours
from ClearMap.Alignment.Resampling import resamplePoints, resamplePointsInverse
from ClearMap.Analysis.Voxelization import voxelize
from ClearMap.Utils.ParameterTools import joinParameter
from ClearMap.IO.clean_table import clean_table
from ClearMap.IO import generate_random_crops
from ClearMap.IO.META import extract_data_parameter,extract_universal_parameter,extract_Segmentation_parameter

# The following are specific to brain atlas. 
# If you are using allen brain atlas, use other files
from ClearMap.Analysis.Label_YK_24FEB22 import countPointsInRegions, labelToName, initialize
from ClearMap.Analysis.Statistics_YK_24FEB22 import thresholdPoints
# For Allen brains
#from ClearMap.Analysis.Label import countPointsInRegions, labelToName, initialize
#from ClearMap.Analysis.Statistics import thresholdPoints

# For Rat brains
#from ClearMap.Analysis.Label_Rat_test import countPointsInRegions, labelToName, initialize
#from ClearMap.Analysis.Statistics import thresholdPoints

from ClearMap.Alignment.Elastix import alignData, transformPoints,transformData



######################### Data parameters

data_parameter           = extract_data_parameter(experiment_file,id_index,sheet_name = 'data_parameter')
atlasParameter           = extract_universal_parameter(variable_file,sheet_name = 'atlasParameter')
CropGeneratingParameter  = extract_universal_parameter(variable_file,sheet_name = 'CropGeneratingParameter')
ResamplingParameter      = extract_universal_parameter(variable_file,sheet_name = 'ResamplingParameter')
StackProcessingParameter = extract_universal_parameter(variable_file,sheet_name = 'StackProcessingParameter')
voxelizeParameter        = extract_universal_parameter(variable_file,sheet_name = 'voxelizeParameter')
thresholdParameter       = extract_universal_parameter(variable_file,sheet_name = 'thresholdParameter')
ImageProcessingMethod = data_parameter['ImageProcessingMethod']
detectSpotsParameter, ImageProcessingParameter = extract_Segmentation_parameter(variable_file, ImageProcessingMethod= ImageProcessingMethod)

##### PARAMETERS SPECIFIC FOR DATA SET
# The path to the data files
BaseDirectory = data_parameter['BaseDirectory'];
metapath = os.path.join(BaseDirectory,'metadata.txt');

# Define what channels will be used for signal and background
# The sturcture here is optimized for LifeCanvas SmartSpim2 images
bg_channel_key      = data_parameter['bg_channel_key']
signal_channel_key  = data_parameter['signal_channel_key']

if 'SmartSpim' in data_parameter['Microscope']:
    signal_ex       = signal_channel_key.split('_')[1] # automatically gets the Exitation laser wave length.
    bg_ex           = bg_channel_key.split('_')[1] # automatically gets the Exitation laser wave length.
    imaging_id      = '_'.join([f for f in os.listdir(os.path.join(BaseDirectory, signal_channel_key)) if '.tif' in f][0].split('_')[:2]) # automatically gets scan specific parameters.

    #Data File and Reference channel File, usually as a sequence of files from the microscope
    #This is adjusted to work with SmartSpim2 data files. Adjust if there is a change in how the data is stored.
    SignalFile      = os.path.join(BaseDirectory,signal_channel_key, imaging_id + '_\d{6}_' + signal_ex + '.tif');
    AutofluoFile    = os.path.join(BaseDirectory,bg_channel_key,  imaging_id + '_\d{6}_' + bg_ex + '.tif');
    
    # Read the metadata file that comes out of the SmartSPIM2
    metadf          = pd.read_csv(metapath, sep='\t', header=0,nrows = 1,encoding= 'unicode_escape')
    xy_res,z_res    = metadf.loc[:,metadf.columns[4:6]].values[0] # This will automatically get the resolution of the data.
else:
    #Data File and Reference channel File, usually as a sequence of files from the microscope
    SignalFile      = os.path.join(BaseDirectory,signal_channel_key, '*.tif');
    AutofluoFile    = os.path.join(BaseDirectory,bg_channel_key,  '*.tif'); 
    xy_res          = data_parameter['xy_res']
    z_res           = data_parameter['z_res']



#Orientation: 1,2,3 means the same orientation as the reference and atlas files.
#Flip axis with - sign (eg. (-1,2,3) flips x). 3D Rotate by swapping numbers. (eg. (2,1,3) swaps x and y)
# If the brain was scanned in horizontal direction, flip the y and z, so (1,3,2).
# If the brain was ventral to dorsal, flip the z, so (1,3,-2).
# If the brain was positioned posterior top, flip the y, so (1,-3,2).
FinalOrientation = data_parameter['FinalOrientation'];

##### 


##### PARAMETERS SPECIFIC FOR ATLAS
#Resolution of the Atlas (in um/ pixel)
AtlasResolution = atlasParameter['AtlasResolution'];

#Path to registration parameters and atlases
PathReg         = atlasParameter['PathReg']; # change this to the path where you store the brain data

AtlasFile       = os.path.join(PathReg,atlasParameter['AtlasFile']); # The image file which contains the MRI scan of mouse brain. This will be used to align the atlas to the raw images.
AnnotationFile  = os.path.join(PathReg,atlasParameter['AnnotationFile']); # The image file which contains the mouse brain with region labels.
AtlasInfoFile   = os.path.join(PathReg,atlasParameter['AtlasInfoFile']); # The table file which contains information about the brain atlas structure. The region "id" listed in this file will be used to decode the regions in "AnnotationFile".

#HRAtlasFile     = os.path.join(PathReg, 'Atlas_HRresampled.tif'); # The high resolution version of the brain atlas. Used for visualization.
#ContourFile	    = os.path.join(PathReg, 'Kim_ref_adult_FP-label_v2.9_contour_map.tif'); 
initialize(annotationFile = AtlasInfoFile); # inialize the annotation file

##### 

#Specify the range for the cell detection. This doesn't affect the resampling and registration operations
SignalFileRange = data_parameter['SignalFileRange'];

#Resolution of the Raw Data (in um / pixel)
OriginalResolution = (xy_res, xy_res, z_res);

######################### Crop generation Parameters

tCropGeneratingParameter = {
    'input_folder'      : os.path.join(BaseDirectory, signal_channel_key), # the input folder which contains the data you want to generate crops. Default to signal folder.
    'output_folder'     : os.path.join(BaseDirectory, signal_channel_key +'_crops'), # the output folder to store the crop data.
    'fkey'              : os.path.basename(BaseDirectory), # identifier for the cropped image. Default will use the folder name.
    } 

CropGeneratingParameter = joinParameter(CropGeneratingParameter, tCropGeneratingParameter)


#################### Heat map generation

##Voxelization: file name for the output:
VoxelizationFile = os.path.join(BaseDirectory, signal_channel_key + '_points_voxelized.tif');

######################## Run Parameters, usually you don't need to change those


### Resample Fluorescent and Signal images
# Autofluorescent Signal resampling for aquisition correction

ResolutionAffineSignalAutoFluo =  atlasParameter['ResolutionAffineSignalAutoFluo'];

CorrectionResamplingParameterSignal = ResamplingParameter.copy();

CorrectionResamplingParameterSignal["source"] = SignalFile;
CorrectionResamplingParameterSignal["sink"]   = os.path.join(BaseDirectory, ''+signal_channel_key+'_resampled.tif');
    
CorrectionResamplingParameterSignal["resolutionSource"] = OriginalResolution;
CorrectionResamplingParameterSignal["resolutionSink"]   = ResolutionAffineSignalAutoFluo;

CorrectionResamplingParameterSignal["orientation"] = FinalOrientation;
    

#Files for Auto-fluorescence for acquisition movements correction
CorrectionResamplingParameterAutoFluo = CorrectionResamplingParameterSignal.copy();
CorrectionResamplingParameterAutoFluo["source"] = AutofluoFile;
CorrectionResamplingParameterAutoFluo["sink"]   = os.path.join(BaseDirectory, 'autofluo_for_'+signal_channel_key+'_resampled.tif');
   
#Files for Auto-fluorescence (Atlas Registration)
RegistrationResamplingParameter = CorrectionResamplingParameterAutoFluo.copy();
RegistrationResamplingParameter["sink"]            =  os.path.join(BaseDirectory, 'autofluo_resampled.tif');
RegistrationResamplingParameter["resolutionSink"]  = AtlasResolution;
   

### Align Signal and Autofluo

CorrectionAlignmentParameter = {            
    #moving and reference images
    "movingImage" : os.path.join(BaseDirectory, 'autofluo_for_'+signal_channel_key+'_resampled.tif'),
    "fixedImage"  : os.path.join(BaseDirectory, ''+signal_channel_key+'_resampled.tif'),
    
    #elastix parameter files for alignment
    "affineParameterFile"  : os.path.join(PathReg, 'Par0000affine_acquisition.txt'),
    "bSplineParameterFile" : None,
    
    #directory of the alignment result
    "resultDirectory" :  os.path.join(BaseDirectory, 'elastix_'+signal_channel_key+'_to_auto')
    }; 
  

### Align Autofluo and Atlas

#directory of the alignment result
RegistrationAlignmentParameter = CorrectionAlignmentParameter.copy();

RegistrationAlignmentParameter["resultDirectory"] = os.path.join(BaseDirectory, 'elastix_auto_to_atlas');
    
#moving and reference images
RegistrationAlignmentParameter["movingImage"]  = AtlasFile;
RegistrationAlignmentParameter["fixedImage"]   = os.path.join(BaseDirectory, 'autofluo_resampled.tif');

#elastix parameter files for alignment
RegistrationAlignmentParameter["affineParameterFile"]  = os.path.join(PathReg, 'Par0000affine.txt');
RegistrationAlignmentParameter["bSplineParameterFile"] = os.path.join(PathReg, 'Par0000bspline.txt');

## Transform the atlas to autofluo
TransformParameter = {};
TransformParameter['sink'] = os.path.join(BaseDirectory, 'aligned_atlas.tif')
TransformParameter['transformDirectory']  = RegistrationAlignmentParameter["resultDirectory"]
TransformParameter['resultDirectory'] = os.path.join(BaseDirectory, 'transform_atlas')
TransformParameter['source'] = AtlasFile

## Transform the contour to autofluo
#ContourTransformParameter = {};
#ContourTransformParameter['sink'] = os.path.join(BaseDirectory, 'aligned_contour.tif')
#ContourTransformParameter['transformDirectory']  = RegistrationAlignmentParameter["resultDirectory"]
#ContourTransformParameter['resultDirectory'] = os.path.join(BaseDirectory, 'transform_contour')
#ContourTransformParameter['source'] = ContourFile


# result files for object coordinates (csv, vtk or ims)
SpotDetectionParameter = {
    "source" : SignalFile,
    "sink"   : (os.path.join(BaseDirectory, signal_channel_key + '_cells-allpoints.npy'),  os.path.join(BaseDirectory,  signal_channel_key + '_intensities-allpoints.npy')),
    "detectSpotsParameter" : detectSpotsParameter
};

SpotDetectionParameter = joinParameter(SpotDetectionParameter, SignalFileRange)
tempImageProcessingParameter = joinParameter(StackProcessingParameter, SpotDetectionParameter);
ImageProcessingParameter = joinParameter(ImageProcessingParameter, tempImageProcessingParameter);


FilteredCellsFile = (os.path.join(BaseDirectory, signal_channel_key + '_cells.npy'), os.path.join(BaseDirectory,  signal_channel_key + '_intensities.npy'));

TransformedCellsFile = os.path.join(BaseDirectory, signal_channel_key + '_transformed_to_Atlas.npy')

### Transform points from Original segmented objects position to autofluorescence

## Transform points from original to corrected
# downscale points to referenece image size

CorrectionResamplingPointsParameter = CorrectionResamplingParameterSignal.copy();
CorrectionResamplingPointsParameter["pointSource"] = os.path.join(BaseDirectory, signal_channel_key + '_cells.npy');
CorrectionResamplingPointsParameter["dataSizeSource"] = SignalFile;
CorrectionResamplingPointsParameter["pointSink"]  = None;

CorrectionResamplingPointsInverseParameter = CorrectionResamplingPointsParameter.copy();
CorrectionResamplingPointsInverseParameter["dataSizeSource"] = SignalFile;
CorrectionResamplingPointsInverseParameter["pointSink"]  = None;

## Transform points from corrected to registered
# downscale points to referenece image size
RegistrationResamplingPointParameter = RegistrationResamplingParameter.copy();
RegistrationResamplingPointParameter["dataSizeSource"] = SignalFile;
RegistrationResamplingPointParameter["pointSink"]  = None;

### Create Contour and overlay with brain
'''
ContourOverlayParameter = {
	"binary_f1_output"		: os.path.join(BaseDirectory, signal_channel_key + '_binary_f1_score.npy'),
	"mri_atlas_image_path"	: os.path.join(BaseDirectory, 'autofluo_resampled.tif');,
	"clearmap_output_image_path":os.path.join(BaseDirectory, 'aligned_atlas.tif') ,
}
'''
### Update the CropGenerationParameters
CropImageProcessingParameter = ImageProcessingParameter.copy()
