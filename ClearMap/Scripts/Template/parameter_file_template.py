# -*- coding: utf-8 -*-
"""
Example script to set up the parameters for the image processing pipeline
"""

######################### Import modules

import os, numpy, math
import sys
import pandas as pd
sys.path.append('.../ClearMap') #ClearMap path

import tempfile
tempfile.gettempdir()
import ClearMap.Settings as settings
import ClearMap.IO as io

from ClearMap.Alignment.Resampling import resampleData;
from ClearMap.Alignment.Elastix import alignData, transformPoints
from ClearMap.ImageProcessing.CellDetection import detectCells
from ClearMap.Alignment.Resampling import resamplePoints, resamplePointsInverse
from ClearMap.Analysis.Voxelization import voxelize
from ClearMap.Utils.ParameterTools import joinParameter
from ClearMap.IO.clean_table import clean_table

# The following are specific to brain atlas. 
# If you are using allen brain atlas, use other files
from ClearMap.Analysis.Label_YK_24FEB22 import countPointsInRegions, labelToName
from ClearMap.Analysis.Statistics_YK_24FEB22 import thresholdPoints
# For Allen brains
#from ClearMap.Analysis.Label_Rat_test import countPointsInRegions, labelToName
#from ClearMap.Analysis.Statistics import thresholdPoints

from ClearMap.Alignment.Elastix import alignData, transformPoints,transformData



######################### Data parameters


##### PARAMETERS SPECIFIC FOR DATA SET
# The path to the data files
BaseDirectory = r'.../DataPath';
metapath = os.path.join(BaseDirectory,'metadata.txt');

# Define what channels will be used for signal and background
bg_channel_key = 'Ex_488_Ch0_stitched' 
signal_channel_key = 'Ex_561_Ch1_stitched'
signal_ex = signal_channel_key.split('_')[1] # automatically gets the Exitation laser wave length.
bg_ex = bg_channel_key.split('_')[1] # automatically gets the Exitation laser wave length.
imaging_id = '_'.join([f for f in os.listdir(os.path.join(BaseDirectory, signal_channel_key)) if '.tif' in f][0].split('_')[:2]) # automatically gets scan specific parameters.

#Orientation: 1,2,3 means the same orientation as the reference and atlas files.
#Flip axis with - sign (eg. (-1,2,3) flips x). 3D Rotate by swapping numbers. (eg. (2,1,3) swaps x and y)
# If the brain was scanned in horizontal direction, flip the y and z, so (1,3,2).
# If the brain was ventral to dorsal, flip the z, so (1,3,-2).
# If the brain was positioned posterior top, flip the y, so (1,-3,2).
FinalOrientation = (1, 3, -2);

##### 

##### PARAMETERS SPECIFIC FOR Ilastik CLASSIFIER
# If you are using SpotDetection, go directly to the Cell Detection Parameters section
ImageProcessingMethod = "Ilastik"; 
classifier_path = r".../Classifier.ilp"

classindex = 0 # Index of the class to be used for spot detection. Depends on how you set labels in Ilastik.
##### 

##### PARAMETERS SPECIFIC FOR ATLAS
#Resolution of the Atlas (in um/ pixel)
AtlasResolution = (20, 20, 50);

#Path to registration parameters and atlases
PathReg        = '.../clearmap_ressources_mouse_brain/ClearMap_ressources/Regions_annotations/'; # change this to the path where you store the brain data
AtlasFile      = os.path.join(PathReg, 'Kim_ref_adult_v1_brain.tif');
AnnotationFile = os.path.join(PathReg, 'Kim_ref_adult_FP-label_v2.0.tif');
AtlasInfoFile = os.path.join(PathReg, 'atlas_info_KimRef_FPbasedLabel_v2.9.csv');

##### 



# Load the meta data file from the SmartSpim2
metadf = pd.read_csv(metapath, sep='\t', header=0,nrows = 1,encoding= 'unicode_escape')
#print(metadf.columns)
xy_res,z_res = metadf.loc[:,metadf.columns[2:4]].values[0] # This will automatically get the resolution of the data.
#print(metadf.loc[:,metadf.columns[2:4]].values[0] )
#Data File and Reference channel File, usually as a sequence of files from the microscope
#This is adjusted to work with SmartSpim2 data files. Adjust if there is a change in how the data is stored.

#SignalFile = os.path.join(BaseDirectory, signal_channel_key, 'cFOS_647_R2_HR_F.ome.tif'); # check if this matches the file name
#AutofluoFile = os.path.join(BaseDirectory, bg_channel_key, 'auto_488_R2_HR_F.ome.tif');
SignalFile = os.path.join(BaseDirectory,signal_channel_key, imaging_id + '_\d{6}_' + signal_ex + '.tif');
AutofluoFile = os.path.join(BaseDirectory,bg_channel_key,  imaging_id + '_\d{6}_' + bg_ex + '.tif');

#Specify the range for the cell detection. This doesn't affect the resampling and registration operations
SignalFileRange = {'x' : all, 'y' : (all), 'z' : all};
#SignalFileRange = {'x' : (3000,5000), 'y' : (3000,5000), 'z' : (1000,1500)};

#Resolution of the Raw Data (in um / pixel)
OriginalResolution = (xy_res, xy_res, z_res);





######################### Cell Detection Parameters using custom filters

#Spot detection method: faster, but optimised for spherical objects.
#You can also use "Ilastik" for more complex objects
ImageProcessingParameter = {
    'method': "Ilastik", # Use "SpotDetection" or "Ilastik"
    'classifier': classifier_path,
    'classindex': classindex, # Index of the class to be used for spot detection. Depends on how you set labels in Ilastik.
}

#For illumination correction (necessitates a specific calibration curve for your microscope)
correctIlluminationParameter = {
    "flatfield"  : None,  # (True or None)  flat field intensities, if None do not correct image for illumination 
    "background" : None, # (None or array) background image as file name or array, if None background is assumed to be zero
    "scaling"    : "Max", # (str or None)        scale the corrected result by this factor, if 'max'/'mean' scale to keep max/mean invariant
    "save"       : None,       # (str or None)        save the corrected image to file
    "verbose"    : True    # (bool or int)        print / plot information about this step 
}

#Remove the background with morphological opening (optimised for spherical objects)
removeBackgroundParameter = {
    "size"    : (4,4),  # size in pixels (x,y) for the structure element of the morphological opening
    "save"    : None,     # file name to save result of this operation
}

#Difference of Gaussians filter: to enhance the edges. Useful if the objects have a non smooth texture (eg: amyloid deposits)
filterDoGParameter = {
    "size"    : (6,6,11),        # (tuple or None)      size for the DoG filter in pixels (x,y,z) if None, do not correct for any background
    "sigma"   : None,        # (tuple or None)      std of outer Gaussian, if None automatically determined from size
    "sigma2"  : None,        # (tuple or None)      std of inner Gaussian, if None automatically determined from size
    "save"    : None,        # (str or None)        file name to save result of this operation if None dont save to file 
    "verbose" : True      # (bool or int)        print / plot information about this step
} 

#Extended maxima: if the peak intensity in the object is surrounded by smaller peaks: avoids overcounting "granular" looking objects
#findExtendedMaximaParameter = {
 #   "hMax"      : None,            # (float or None)     h parameter (for instance 20) for the initial h-Max transform, if None, do not perform a h-max transform
  #  "size"      : 5,             # (tuple)             size for the structure element for the local maxima filter
   # "threshold" : 0,        # (float or None)     include only maxima larger than a threshold, if None keep all local maxima
    #"save"      : None,         # (str or None)       file name to save result of this operation if None dont save to file 
    #"verbose"   : True       # (bool or int)       print / plot information about this step
#}

#If no cell shape detection and the maximum intensity is not at the gravity center of the object, look for a peak intensity around the center of mass. 
findIntensityParameter = {
    "method" : 'Max',       # (str, func, None)   method to use to determine intensity (e.g. "Max" or "Mean") if None take intensities at the given pixels
    "size"   : (3,3,3)      # (tuple)             size of the search box on which to perform the *method*
}

#Object volume detection. The object is painted by a watershed, until reaching the intensity threshold, based on the background subtracted image
detectCellShapeParameter = {
    "threshold" : (50),     # (float or None)      threshold to determine mask. Pixels below this are background if None no mask is generated
    "save"      : None,        # (str or None)        file name to save result of this operation if None dont save to file 
    "verbose"   : True      # (bool or int)        print / plot information about this step if None take intensities at the given pixels
}


 ## Parameters for cell detection using spot detection algorithm 
detectSpotsParameter = {
    "correctIlluminationParameter" : correctIlluminationParameter,
    "removeBackgroundParameter"    : removeBackgroundParameter,
    "filterDoGParameter"           : filterDoGParameter,
   # "findExtendedMaximaParameter"  : findExtendedMaximaParameter,
    "findIntensityParameter"       : findIntensityParameter,
    "detectCellShapeParameter"     : detectCellShapeParameter
} 





#################### Heat map generation

##Voxelization: file name for the output:
VoxelizationFile = os.path.join(BaseDirectory, signal_channel_key + '_points_voxelized.tif');

# Parameter to calculate the density of the voxelization
voxelizeParameter = {
    #Method to voxelize
    "method" : 'Spherical', # Spherical,'Rectangular, Gaussian'
       
    # Define bounds of the volume to be voxelized in pixels
    "size" : (10,10,10),  

    # Voxelization weigths (e/g intensities)
    "weights" : None
};





############################ Config parameters

#Processes to use for Resampling (usually twice the number of physical processors)
ResamplingParameter = {
    "processes": 48
};


#Stack Processing Parameter for cell detection
StackProcessingParameter = {
    #max number of parallel processes. Be careful of the memory footprint of each process!
    "processes" : 20,
   
    #chunk sizes: number of planes processed at once
    "chunkSizeMax" : 500,
    "chunkSizeMin" : 400,
    "chunkOverlap" : 40,

    #optimize chunk size and number to number of processes to limit the number of cycles
    "chunkOptimization" : False,
    
    #increase chunk size for optimization (True, False or all = automatic)
    "chunkOptimizationSize" : False,
   
    "processMethod" : "parallel"
   };






######################## Run Parameters, usually you don't need to change those


### Resample Fluorescent and Signal images
# Autofluorescent Signal resampling for aquisition correction

ResolutionAffineSignalAutoFluo =  (16, 16, 16);

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

