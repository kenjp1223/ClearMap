# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from setuptools.extension import Extension
from Cython.Build import cythonize

import ClearMap
import numpy

with open('README.md') as fptr:
    readme = fptr.read()

with open('LICENSE.txt') as fptr:
    license = fptr.read()

extensions = [Extension(
        "ClearMap/Analysis/VoxelizationCode",
        ["ClearMap/Analysis/VoxelizationCode.pyx"],
        include_dirs=[numpy.get_include()],
    )
]

setup(
    name             = ClearMap.__title__,
    version          = ClearMap.__version__,
    description      = 'ClearMap 1 fork adapted for batch processing on SLURM/Singularity HPC clusters',
    long_description = readme,
    long_description_content_type = 'text/markdown',
    author           = "Kentaro Ishii",
    author_email     = 'ken1223@uw.edu',
    url              = 'https://github.com/kenjp1223/ClearMap',
    license          = license,
    packages         = find_packages(exclude=('tests', 'docs')),
    ext_modules      = cythonize(extensions),
    python_requires  = '>=2.7, <3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Image Processing',
    ],
)
