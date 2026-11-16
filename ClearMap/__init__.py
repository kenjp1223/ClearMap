# -*- coding: utf-8 -*-
"""
*ClearMap* is a python toolbox for the analysis and registration of volumetric
data from cleared tissues obtained with Light Sheet microscopy.

This is the Stuber Lab (University of Washington) fork of ClearMap 1, adapted for
batch processing on SLURM clusters inside a Singularity/Apptainer container.
See https://github.com/kenjp1223/ClearMap for the HPC workflow.

The ClearMap code package is structured into four main modules:

   * **IO** for reading and writing images and data
   * **Alignment** for resampling, reorientation and registration of images onto references
   * **Image Processing** for correcting and quantifying the image data
   * **Analysis** for the statistical analysis of the data

Note:
    This code base targets Python 2.7.

"""

__title__ = 'ClearMap'

__version__ = '0.9.2+hpc'

__author__ = 'Christoph Kirst; HPC fork: Kentaro Ishii'

__license__ = 'GNU GENERAL PUBLIC LICENSE Version 3'

__copyright__ = '2016 Christoph Kirst; 2024-2026 Kentaro Ishii'

__all__ = ["Settings", "Parameter", "IO", "ImageProcessing", "Analysis"]

import ClearMap.Settings
import ClearMap.Parameter
