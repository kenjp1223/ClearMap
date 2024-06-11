# -*- coding: utf-8 -*-
"""
Template to run the overlap analysis
"""
import time
from ClearMap.Analysis.overlap_detection import find_overlap

start = time.time()

print("Start analysis")

#load the parameters:
execfile('.../parameter_file_template.py') #user specific
signal_channel1_key = 'Ex_561_Ch1_stitched'
signal_channel1_key = 'Ex_639_Ch2_stitched'

# read sample images to detect the shape of the images
imshape = io.dataSize(os.path.join(BaseDirectory, signal_channel1_key))

# read sample images to detect the shape of the images
overlapcellarray,__,__,__ = find_overlap(
    os.path.join(BaseDirectory,signal_channel1_key + '_cells.npy'),
    os.path.join(BaseDirectory,signal_channel2_key + '_cells.npy'),
    imshape,
    offset = (3,3,3),
    save_bool = True)

# save the overlap cell array
np.save(os.path.join(BaseDirectory,'overlap_stitched_cells.npy'),overlapcellarray)

# Transform point coordinates
#############################
# Update source information to the new overlap file
CorrectionResamplingPointsParameter["pointSource"] = os.path.join(BaseDirectory,'overlap_stitched_cells.npy');

points = io.readPoints(os.path.join(BaseDirectory,'overlap_stitched_cells.npy'));
points = resamplePoints(**CorrectionResamplingPointsParameter);
points = transformPoints(points, transformDirectory = CorrectionAlignmentParameter["resultDirectory"], indices = False, resultDirectory = None);
CorrectionResamplingPointsInverseParameter["pointSource"] = points;
points = resamplePointsInverse(**CorrectionResamplingPointsInverseParameter);
RegistrationResamplingPointParameter["pointSource"] = points;
points = resamplePoints(**RegistrationResamplingPointParameter);
points = transformPoints(points, transformDirectory = RegistrationAlignmentParameter["resultDirectory"], indices = False, resultDirectory = None);
io.writePoints(os.path.join(BaseDirectory, 'overlap_transformed_to_Atlas.npy'), points);

# Heat map generation
#####################
points = io.readPoints(os.path.join(BaseDirectory, 'overlap_transformed_to_Atlas.npy'))
#intensities = io.readPoints(FilteredCellsFile[1])

#Without weigths:
vox = voxelize(points, AtlasFile, **voxelizeParameter);
if not isinstance(vox, basestring):
   io.writeData(os.path.join(BaseDirectory, 'overlap_cells_heatmap.tif'), vox.astype('int32'));


#Table generation:
##################
#With integrated weigths from the intensity file (here raw intensity):
#ids, counts = countPointsInRegions(points, labeledImage = AnnotationFile, intensities = intensities, intensityRow = 0);
#table = numpy.zeros(ids.shape, dtype=[('id','int64'),('counts','f8'),('name', 'a256')])
#table["id"] = ids;
#table["counts"] = counts;
#table["name"] = labelToName(ids);
#io.writeTable(os.path.join(BaseDirectory, 'Annotated_counts_intensities.csv'), table);

#Without weigths (pure cell number):
ids, counts = countPointsInRegions(points, labeledImage = AnnotationFile, intensities = None, collapse = None);
table = numpy.zeros(ids.shape, dtype=[('id','int64'),('counts','f8'),('name', 'a256')])
table["id"] = ids;
table["counts"] = counts;
table["name"] = labelToName(ids);
io.writeTable(os.path.join(BaseDirectory, 'overlap_Annotated_counts.csv'), table);

#####################

#clean_table(os.path.join(BaseDirectory, 'Annotated_counts_intensities.csv'),AtlasInfoFile)
clean_table(os.path.join(BaseDirectory, 'overlap_Annotated_counts.csv'),AtlasInfoFile)


#####################

# Fin
end = time.time()
print("The entire process ended in ",end - start)
