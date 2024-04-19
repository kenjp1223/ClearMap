#!/usr/bin/env python
# encoding: utf-8

"""
Functions that are used to gather experiment meta data.


Author
""""""
    Added into ClearMap framework by Kentaro Ishii, The University Washington, Seattle, 2024

"""



import os
import pandas as pd
import numpy as np

def extract_data_parameter(experiment_file,id_index,):
    #############################
    # Extract data specific parameters
    #############################
    df = pd.read_csv(experiment_file,index_col = False)
    
    # convert dataframe to dictionary
    data_parameter_dict = df.loc[id_index,:].to_dict()

    # reformat the tuple parameters
    for key in data_parameter_dict.keys():
        try:
            data_parameter_dict[key] = eval(data_parameter_dict[key])
        except:
            pass
    
    return data_parameter_dict

def extract_universal_parameter(experiment_file,sheet_name = 'atlasParameter'):
    #############################
    # Extract universal parameters
    #############################
    df = pd.read_excel(experiment_file,sheet_name = sheet_name)
    df = df.replace({np.nan: None})
    
    # convert dataframe to dictionary
    if not sheet_name == 'thresholdParameter':
        data_parameter_dict = df.to_dict('records')[0]
        # reformat the tuple parameters
        for key in data_parameter_dict.keys():
            try:
                data_parameter_dict[key] = eval(data_parameter_dict[key])
            except:
                pass

    else:
        data_parameter_dict = df.to_dict('list')
        for key in data_parameter_dict.keys():
            try:
                data_parameter_dict[key] = [eval(f) for f in data_parameter_dict[key]]
            except:
                pass
   
    return data_parameter_dict

def extract_Segmentation_parameter(experiment_file, ImageProcessingMethod='SpotDetection'):
    """
    Extracts segmentation parameters based on the specified ImageProcessingMethod.
    
    Parameters:
        experiment_file (str): Path to the Excel file containing parameters.
        ImageProcessingMethod (str): Method used for image processing.
    
    Returns:
        dict: Dictionary containing extracted parameters.
    """
    # Spot Detection parameters extraction
    if ImageProcessingMethod == 'SpotDetection':
        df = pd.read_excel(experiment_file, sheet_name='SpotDetectionParameter',header = [0,1])
        df = df.replace({np.nan: None})
        # Initialize an empty dictionary
        detectSpotsParameter = {}

        # Iterate through the columns
        for col in df.columns:
            # Get the first and second level of the multi-index
            first_key, second_key = col
            
            # If the first key is not in the data_parameter_dict, add it
            if first_key not in detectSpotsParameter:
                detectSpotsParameter[first_key] = {}
            
            # Add the value to the dictionary under the first and second keys
            try:
                detectSpotsParameter[first_key][second_key] = eval(df[col][0])
            except:
                detectSpotsParameter[first_key][second_key] = df[col][0]
            
        ImageProcessingParameter = {'method':ImageProcessingMethod}
    # Ilastik parameters extraction
    elif ImageProcessingMethod == 'Ilastik':
        ImageProcessingParameter = extract_universal_parameter(experiment_file, sheet_name='ilastikParameter')
        ImageProcessingParameter['method'] = ImageProcessingMethod
        detectSpotsParameter = {}
    else:
        print("Segmentation algorithm was not found...")
        raise ValueError("Segmentation algorithm was not found.")

    return detectSpotsParameter, ImageProcessingParameter
