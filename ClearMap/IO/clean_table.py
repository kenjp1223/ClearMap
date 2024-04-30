#####################

import pandas as pd
import csv
import numpy as np
import os
######################### 

def get_subregions(dataframe, region_id, collected=None, return_original=False):
    """
    Recursively get all subregions of a given region_id from the dataframe.

    Args:
        dataframe (pandas.DataFrame): DataFrame containing brain region data.
        region_id (int): ID of the region to get subregions for.
        collected (list, optional): List to store collected subregions. Defaults to None.

    Returns:
        pandas.DataFrame: DataFrame of subregions.
    """
    if collected is None:
        collected = []

    # Find subregions of the current region_id
    subregions = dataframe[dataframe['parent_id'] == region_id].to_dict('records')

    # Add current subregions to the collected list
    collected.extend(subregions)

    # Recursively search for subregions of each subregion
    for subregion in subregions:
        get_subregions(dataframe, subregion['id'], collected)

    if return_original:
        original = dataframe[dataframe['id'] == region_id].to_dict('records')
        collected.extend(original)
        return_original = False

    return pd.DataFrame(collected)

def clean_table(csvname,AtlasInfoFile):
    row = []
    longest = 0
    #find longest row
    with open(csvname,'rb') as csvfile:
        reader = csv.reader(csvfile)
        for i in reader:
            if len(i) > longest:
                longest = len(i)

    #for temp column
    namecol = longest - 3
    tmpcol = []

    for i in range(namecol):
        tmpcol.append('col_'+str(i))

    std_col = ['id','counts','Name'] #original column
    col_names = std_col + tmpcol
    df = pd.read_csv(csvname,names=col_names) #read csv

    #replace nan with str
    tmpdf = df[df.columns[-namecol:]].replace(np.NaN,'')
    newname = df.Name

    #get full name
    for i in tmpdf.columns:
            newname += tmpdf[i]

    # replace new name to df
    df = df[std_col]
    df.Name = newname


    df2 = pd.read_csv(AtlasInfoFile)
    df2 = df2[['id','structure_order','parent_id','parent_acronym','acronym']]

    #sort
    df = df.set_index('id')
    df = df.reindex(list(df2.id))
    df.reset_index(inplace=True)

    #concat
    if list(df.id) == list(df2.id):
        df2 = df2[['structure_order','parent_id','parent_acronym','acronym']]
        finaldf = pd.concat([df,df2],axis=1)

    #get sorted id from children to parent
    id_sorted = []
    for i in list(finaldf.id)[::-1]:
        if i in np.unique(finaldf.parent_id):
            id_sorted.append(i)

    #add new col
    finaldf['newcounts'] = 0

    for iid in finaldf.id:
        tdf = get_subregions(finaldf, iid, return_original = True)
        finaldf.loc[finaldf.id == iid,'newcounts'] = np.sum(tdf.counts)    
    
    
    '''
    #add new col
    finaldf['newcounts'] = finaldf.counts

    #add newcounts
    for i in id_sorted:
        idx = finaldf[finaldf.id == i].index
        totalchildrencount = sum(finaldf[finaldf.parent_id == i].newcounts)
        parentcount = finaldf.counts.loc[idx]
        finaldf.newcounts.loc[idx] = parentcount + totalchildrencount
    '''
    finaldf = finaldf[['id','counts','newcounts','Name','structure_order','parent_id','parent_acronym','acronym']]
    #return finaldf
    finaldf.to_csv(csvname.replace('.csv','_clean.csv'),index=False)



