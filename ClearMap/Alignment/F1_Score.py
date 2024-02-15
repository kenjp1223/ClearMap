import tifffile
import cv2
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import sklearn.metrics as sk


#mri_atlas_image_path = r"Atlas\aligned_atlas_original.tif"
#clearmap_output_image_path = r"Data\autofluo_resampled_original.tif"

# returns the loaded images indicated by the file paths
def LoadingData(mri_atlas_image_path, clearmap_output_image_path):
    mri_atlas_image = tifffile.imread(mri_atlas_image_path)
    clearmap_output_image = tifffile.imread(clearmap_output_image_path)
    
    return mri_atlas_image, clearmap_output_image

# returns an array of F1 score per slice calculated by comparing 
# the filled contours drawn around each image
# the input is only the loaded images
def F1Scores_WithContours(mri_atlas_image_path, clearmap_output_image_path,binary_f1_outputpath):
    mri_atlas_image, clearmap_output_image = LoadingData(mri_atlas_image_path, clearmap_output_image_path)
    # calculating f1 score for all slices
    depth = len(mri_atlas_image)
    binary_f1_output = np.empty(depth)

    # iterating through brain slices
    for i in range(depth):

        # loading the indicated slice
        tmpimg = mri_atlas_image[i,:,:]
        outputimg = clearmap_output_image[i,:,:]
        
        # 8-bit conversion
        tmpimg = (tmpimg).astype('uint8')
        outputimg = (outputimg).astype('uint8')

        # automatic thresholding
        _, thresh_atlas = cv2.threshold(tmpimg,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        _, thresh_output = cv2.threshold(outputimg,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

        # detect and draw contours for binary image of atlas and registered image
        contours_atlas, _ = cv2.findContours(image=thresh_atlas, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_NONE)
        image_copy_atlas = tmpimg.copy()
        contours_atlas = cv2.drawContours(image=image_copy_atlas, contours=contours_atlas, contourIdx=-1, color=(255, 255, 0), thickness=cv2.FILLED, lineType=cv2.LINE_AA)

        contours_output, _ = cv2.findContours(image=thresh_output, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_NONE)
        image_copy_output = outputimg.copy()
        contours_output = cv2.drawContours(image=image_copy_output, contours=contours_output, contourIdx=-1, color=(255, 255, 0), thickness=cv2.FILLED, lineType=cv2.LINE_AA)

        # automatic threshold again for F1 score calculation
        _, final_thresh_atlas = cv2.threshold(contours_atlas,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        _, final_thresh_output = cv2.threshold(contours_output,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

        # 1 score calculation
        f1_score = sk.f1_score(final_thresh_atlas.flatten(), final_thresh_output.flatten(), pos_label=255)

        # storing results per slice
        binary_f1_output[i] = f1_score
    np.save(binary_f1_outputpath,binary_f1_output)
    print("Result of the average alignment was F1 score: ",np.nanmean(binary_f1_output), " +/- ", np.nanstd(binary_f1_output))
    return binary_f1_output    

# returns an array of F1 score per slice calculated by comparing
# the raw binary-thresholded images
# the input is only the loaded images
def F1Scores_NoContours(mri_atlas_image_path, clearmap_output_image_path,binary_f1_outputpath):
    mri_atlas_image, clearmap_output_image = LoadingData(mri_atlas_image_path, clearmap_output_image_path)
    # calculating f1 score for all slices
    depth = len(mri_atlas_image)
    binary_f1_output = np.empty(depth)

    # iterating through brain slices
    for i in range(depth):

        # loading the indicated slice
        tmpimg = mri_atlas_image[i,:,:]
        outputimg = clearmap_output_image[i,:,:]
        
        # 8-bit conversion
        tmpimg = (tmpimg).astype('uint8')
        outputimg = (outputimg).astype('uint8')

        # automatic thresholding
        _, thresh_atlas = cv2.threshold(tmpimg,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        _, thresh_output = cv2.threshold(outputimg,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

        # f1 score calculation
        f1_score = sk.f1_score(thresh_atlas.flatten(), thresh_output.flatten(), pos_label=255)

        # storing results per slice
        binary_f1_output[i] = f1_score
    np.save(binary_f1_outputpath,binary_f1_output)
    print("Result of the average alignment was F1 score: ",np.nanmean(binary_f1_output), " +/- ", np.nanstd(binary_f1_output))
    return binary_f1_output

# plots the array of F1 score per slice
# the input is the array of F1 scores from either F1Scores function
def plotF1(binary_f1_output):
	fig, axs = plt.subplots(1, 1, figsize=(5, 5))
	axs.plot(binary_f1_output, color="red", label="positive control")
	axs.set_title("F1 Score Comparing Atlas and Registered Image per Slice")
	axs.set_xlabel("z-axis slice")
	axs.set_ylabel("F1 Score")
	axs.set_ylim(0, 1)
	axs.legend()
	fig.savefig(plot_outputfile, bbox_inches='tight', dpi=216)