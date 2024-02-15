import tifffile
import cv2
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import sklearn.metrics as sk

#annotated_atlas_path = r"\\128.95.12.251\Analysis2\Ken\ClearMap\clearmap_ressources_mouse_brain\ClearMap_ressources\Regions_annotations\Kim_ref_adult_FP-label_v2.8.tif"
#clearmap_output_image_path = r"Data\autofluo_resampled_original.tif"
#fpath = "final_contour_map.tif"

# returns the loaded data indicated by the file paths
def ContourLoadingData(annotated_atlas_path):
    label_atlas_image = tifffile.imread(annotated_atlas_path)

    return label_atlas_image

# returns a tiff file
def LabelledContourDetection(annotated_atlas_path, fpath):
    label_atlas_image = ContourLoadingData(annotated_atlas_path)
    final_contour_map = []

    # iterates over every slice
    for i in range(np.shape(label_atlas_image)[0]):
        labelimg = label_atlas_image[i,:,:]
        contour_slice = []

        # iterates over every subregion in the current slice
        for region_index in np.unique(labelimg):
            if (region_index != 0):
                subregion = (labelimg == region_index)
                subregion = 1*subregion
                subregion = (subregion).astype('uint8')

                # contours the subregion in this iteration
                contours_label, _ = cv2.findContours(image=subregion, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_NONE)
                for element in contours_label:
                    for i in range(np.shape(element)[0]):
                        contour_slice.append(element[i][0])
        final_contour_map.append(contour_slice)

    # converting the coordinates of the contours into a binary image and exporting as a tiff
    binary_contour_full = []
    for slice in final_contour_map:
        binary_contour = np.zeros(np.shape(labelimg))
        for point in slice:
            binary_contour[point[1]][point[0]] = 1
        binary_contour_full.append(binary_contour)

    # writing the data
    tifffile.imwrite(fpath, np.array(binary_contour_full, dtype = np.int32))

#LabelledContourDetection(annotated_atlas_path, clearmap_output_image_path, fpath)