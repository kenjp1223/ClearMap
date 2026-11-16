Installation
============

This fork is deployed as a Singularity/Apptainer container on a SLURM cluster. The container
pins Python 2.7, elastix 4.9.0 and ilastik 1.3.3post3, which is the environment the ClearMap 1
code base expects.

Requirements
^^^^^^^^^^^^

* A SLURM cluster with Singularity or Apptainer available on the compute nodes
* Enough memory for a whole-brain stack — the batch scripts request ~175 GB and 24 cores per
  sample by default
* Fast scratch storage for the resampled stacks and registration output
* The ClearMap atlas resources (``clearmap_ressources_mouse_brain``)

Getting the container
^^^^^^^^^^^^^^^^^^^^^

Pull the prebuilt image:

.. code-block:: bash

    $ singularity pull clearmap.sif library://kishii1223/repo/clearmap

or build it from the definition file in this repository:

.. code-block:: bash

    $ sudo singularity build clearmap.sif ClearMap/Scripts/HPC_clearmap.def

.. note::

   The ``%files`` section of ``HPC_clearmap.def`` copies ``requirements.txt`` from a hard-coded
   path on UW's Klone cluster. Edit it to point at your own checkout before building.

The image clones this repository to ``/ClearMap`` at build time and adds it to ``PYTHONPATH``.
To run a newer working copy, bind-mount it:

.. code-block:: bash

    $ singularity exec -B /path/to/ClearMap:/mnt/ClearMap \
        --env PYTHONPATH=/mnt/ClearMap clearmap.sif python your_script.py

Configuration
^^^^^^^^^^^^^

``ClearMap.Settings`` finds elastix and ilastik from environment variables, falling back to a
table of known hosts:

.. code-block:: bash

    $ export CLEARMAP_ELASTIX_PATH=/elastix-4.9.0-linux
    $ export CLEARMAP_ILASTIK_PATH=/ilastik-1.3.3post3-Linux

ilastik is only needed for classifier-based segmentation; spot detection works without it.

Local installation (without the container)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Possible but not recommended, since it needs a Python 2.7 environment:

.. code-block:: bash

    $ git clone https://github.com/kenjp1223/ClearMap.git
    $ cd ClearMap
    $ pip install -r ClearMap/Scripts/requirements.txt
    $ pip install -e .

``pip install -e .`` compiles the Cython voxelization extension, so a C compiler and numpy
headers are required.

Running the pipeline
^^^^^^^^^^^^^^^^^^^^

See the README for the batch workflow: fill in ``experiment_parameter_tests.csv`` and
``variable_file.xlsx``, edit the header of ``batch_submit_jobs.sh``, and run it to generate and
submit one SLURM job per sample.
