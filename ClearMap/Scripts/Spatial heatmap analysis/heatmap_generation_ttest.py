# run this in python

import os
import numpy as np
import pandas as pd
import tifffile
from scipy import stats

# read clearmap functions
import ClearMap.Analysis.Statistics as stat
import ClearMap.IO.IO as io
from ClearMap.Alignment.Resampling import sagittalToCoronalData
import numpy, os

from scipy import stats


def cutoffPValues(pvals, pcutoff = 0.05):
    if pcutoff is None:
        return pvals;
    
    pvals2 = pvals.copy();
    pvals2[pvals2 > pcutoff]  = pcutoff;
    return pvals2;

def colorPValues(pvals, psign, positive = [1,0], negative = [0,1], pcutoff = None,\
     positivetrend = [0,0,1,0], negativetrend = [0,0,0,1], pmax = None):
    
    pvalsinv = pvals.copy();
    if pmax is None:
        pmax = pvals.max();    
    pvalsinv = pmax - pvalsinv;    
    
    if pcutoff is None:  # color given p values
        
        d = len(positive);
        ds = pvals.shape + (d,);
        pvc = np.zeros(ds);
    
        #color
        ids = psign > 0;
        pvalsi = pvalsinv[ids];
        for i in range(d):
            pvc[ids, i] = pvalsi * positive[i];
    
        ids = psign < 0;
        pvalsi = pvalsinv[ids];
        for i in range(d):
            pvc[ids, i] = pvalsi * negative[i];
        
        return pvc;
        
    else:  # split pvalues according to cutoff
    
        d = len(positivetrend);
        
        if d != len(positive) or  d != len(negative) or  d != len(negativetrend) :
            raise RuntimeError('colorPValues: postive, negative, postivetrend and negativetrend option must be equal length!');
        
        ds = pvals.shape + (d,);
        pvc = np.zeros(ds);
    
        idc = pvals < pcutoff;
        ids = psign > 0;

        ##color 
        # significant postive
        ii = np.logical_and(ids, idc);
        pvalsi = pvalsinv[ii];
        w = positive;
        for i in range(d):
            pvc[ii, i] = pvalsi * w[i];
    
        #non significant postive
        ii = np.logical_and(ids, np.negative(idc));
        pvalsi = pvalsinv[ii];
        w = positivetrend;
        for i in range(d):
            pvc[ii, i] = pvalsi * w[i];
            
         # significant negative
        ii = np.logical_and(np.negative(ids), idc);
        pvalsi = pvalsinv[ii];
        w = negative;
        for i in range(d):
            pvc[ii, i] = pvalsi * w[i];
    
        #non significant postive
        ii = np.logical_and(np.negative(ids), np.negative(idc))
        pvalsi = pvalsinv[ii];
        w = negativetrend;
        for i in range(d):
            pvc[ii, i] = pvalsi * w[i];
        
        return pvc;


################################################################
# data relevant parameters
# read the csv file
# read the experiment file
# specify the path as variable experiment_file
experiment_file = os.environ.get('experiment_file')
metadf = pd.read_csv(experiment_file,index_col = False) #CHANGE HERE

# set where you want to create a result path
rootpath = os.environ.get('rootpath')

################################
# stat relevant parameters
# control group for ttest analysis
control_condition = os.environ.get('control_condition') # 'Vehicle'
pcutoff = os.environ.get('pcutoff') # 'Vehicle'
removeNaN = True

# set output directory
outputpath = os.path.join(rootpath,'result')
# create output directory
if not os.path.exists(outputpath):
    os.mkdir(outputpath)


# loop over rows in the dataframe
heatmap_dict = {}
for Condition in metadf.Condition.unique():
    tIDs = metadf[metadf.Condition == Condition].ID.values
    print(tIDs)
    # create heatmap dictionary
    heatmap_dict[Condition] = []
    # loop over IDs and concatenate the 3d heatmap into dictionary
    for ID in tIDs:
        BaseDirectory = metadf[metadf.ID == ID].BaseDirectory.values[0]
        #print(BaseDirectory)
        theatmatppath   = os.path.join(BaseDirectory,'Ex_639_Ch2_stitched_cells_heatmap.tif')
        if os.path.exists(theatmatppath):
            # read heatmap
            theatmapimg     = tifffile.imread(theatmatppath)
            # concatenate heatmap to dictionary
            heatmap_dict[Condition].append(theatmapimg)
    heatmap_dict[Condition] = np.array(heatmap_dict[Condition])
    print(heatmap_dict[Condition].shape)
    # save heatmap as tiff
    tifffile.imsave(os.path.join(outputpath,Condition.replace('/','-') + '_mean_cells_heatmap.tif'),np.mean(heatmap_dict[Condition],axis = 0).astype('uint16'))

# run stats
for test_condition in metadf.Condition.unique():
    if test_condition == control_condition:
        continue
    sarray = np.array(heatmap_dict[control_condition]).astype('float')
    tarray = np.array(heatmap_dict[test_condition]).astype('float')

    # test ttest
    tvals, pvals = stats.ttest_ind(sarray, tarray, axis = 0, equal_var = True);

    #remove nans
    if removeNaN: 
        pi = np.isnan(pvals);
        print(pi)
        pvals[pi] = 1.0;
        tvals[pi] = 0;

    
    pvals = cutoffPValues(pvals, pcutoff = pcutoff);
    tvals = np.sign(tvals)

    cimg = colorPValues(pvals, tvals, positive = [1,0], negative = [0,1], )


    tifffile.imsave(os.path.join(outputpath, 'positive' + control_condition.replace('/','-') + '_vs_' + test_condition.replace('/','-') + '_pvalues.tif')\
        ,cimg[:,:,:,0].astype('float32'))  
    tifffile.imsave(os.path.join(outputpath, 'negative' + control_condition.replace('/','-') + '_vs_' + test_condition.replace('/','-') + '_pvalues.tif')\
        ,cimg[:,:,:,1].astype('float32'))  
    #io.writeData(os.path.join(outputpath, control_condition.replace('/','-') + '_vs_' + test_condition.replace('/','-') + '_pvalues.tif'), \
    #            sagittalToCoronalData(pvalscolor.astype('float32')));






