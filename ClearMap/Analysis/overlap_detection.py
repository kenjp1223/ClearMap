# -*- coding: utf-8 -*-
"""
Create functions that can be used to detect overlap between two channels.


"""
import numpy as np
from scipy.spatial import cKDTree

# remove due to inefficient overlap detection
'''
def find_overlap(cellarray1path,cellarray2path,imshape,offset = (5,5,3),save_bool = False):
    ######################################
    # find overlapping cells from two arrays of cell coordinate (x,y,z)
    # cellarraypath points to npy files containing the cell coordinate
    # offset: overlap will allow difference of position (x,y,z) in pixels
    ######################################

    # load cell arrays
    cellarray1 = np.load(cellarray1path)
    cellarray2 = np.load(cellarray2path)
    # make sure they are integers
    cellarray1 = cellarray1.astype('int')
    cellarray2 = cellarray2.astype('int')

    # create empty images to check overlap
    img1 = np.zeros(imshape,dtype = 'bool')
    img2 = np.zeros(imshape,dtype = 'bool')

    # update the empty images with cell masks
    for idx,coord in enumerate(cellarray1):
        img1[
        slice(coord[2]-offset[2],coord[2]+offset[2]),
        slice(coord[1]-offset[1],coord[1]+offset[1]),
        slice(coord[0]-offset[0],coord[0]+offset[0])] = True

    for idx,coord in enumerate(cellarray2):
        img2[
        slice(coord[2]-offset[2],coord[2]+offset[2]),
        slice(coord[1]-offset[1],coord[1]+offset[1]),
        slice(coord[0]-offset[0],coord[0]+offset[0])] = True

    # find the masks that overlap with two images
    overlapimg = img1 & img2

    # find the cell indexes that are overlapping with the other array
    boolarray1 = np.array([overlapimg[f[2],f[1],f[0]] for f in cellarray1])
    boolarray2 = np.array([overlapimg[f[2],f[1],f[0]] for f in cellarray2])
   
    # return the final overlap cell coordinate array
    if np.sum(boolarray1) > np.sum(boolarray2):
        overlapcellarray = cellarray2[boolarray2]
    else:
        overlapcellarray = cellarray1[boolarray1]
    
    # save the boolean array
    if save_bool:
        np.save(cellarray1path.replace('.npy','_boolean.npy'),boolarray1)
        np.save(cellarray2path.replace('.npy','_boolean.npy'),boolarray2)
    
    return overlapcellarray,overlapimg,boolarray1,boolarray2
'''



def find_overlap(cellarray1path, cellarray2path, offset=(5,5,3), save_bool=False):
    """
    Identify overlapping cells between two cell coordinate arrays using a proximity threshold.
    
    Parameters:
        cellarray1path (str): Path to .npy file with cell coordinates (x,y,z)
        cellarray2path (str): Path to .npy file with cell coordinates (x,y,z)
        offset (tuple): Max (x,y,z) distance allowed for overlap
        save_bool (bool): Whether to save boolean overlap arrays

    Returns:
        overlap_coords (np.ndarray): Coordinates of overlapping cells (from cellarray1)
        boolarray1 (np.ndarray): Boolean array for cellarray1 indicating overlap
        boolarray2 (np.ndarray): Boolean array for cellarray2 indicating overlap
    """
    cellarray1 = np.load(cellarray1path).astype(int)
    cellarray2 = np.load(cellarray2path).astype(int)

    # Convert anisotropic offset to a distance threshold
    offset = np.array(offset)
    dist_thresh = np.linalg.norm(offset)

    # Build KD-tree for fast spatial search
    tree2 = cKDTree(cellarray2)
    distances, indices = tree2.query(cellarray1, distance_upper_bound=dist_thresh)

    boolarray1 = distances != np.inf
    matched_indices = indices[boolarray1]

    boolarray2 = np.zeros(len(cellarray2), dtype=bool)
    # Mark those in cellarray2 that were matched (avoid double-counting)
    for idx in matched_indices:
        if idx < len(boolarray2):  # filter invalid (out-of-bounds) matches
            boolarray2[idx] = True

    overlap_coords = cellarray1[boolarray1]

    if save_bool:
        np.save(cellarray1path.replace('.npy','_boolean.npy'), boolarray1)
        np.save(cellarray2path.replace('.npy','_boolean.npy'), boolarray2)

    return overlap_coords, boolarray1, boolarray2


