# -*- coding: utf-8 -*-
"""
Create functions that can be used to detect overlap between two channels.


"""
import numpy as np


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

