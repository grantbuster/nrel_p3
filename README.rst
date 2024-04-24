***********************************
NREL Personal Project Planning (P3)
***********************************

Code for doing personal project planning for NREL projects using workday and
pricing tool exports.

See the example `here <https://grantbuster.github.io/nrel_p3/example.html>`_ to get started.

Installing nrel_p3
==================

.. inclusion-install

#. Clone the repo: ``git clone git@github.com:grantbuster/nrel_p3.git``
#. Create ``nrel_p3`` environment and install package
    a) Create a conda env: ``conda create -n p3``
    b) Run the command: ``conda activate p3``
    c) ``cd`` into the repo cloned in 1.
    d) Prior to running ``pip`` below, make sure the branch is correct (install
       from main!)
    e) Install ``nrel_p3`` and its dependencies by running:
       ``pip install .`` (or ``pip install -e .`` if running a dev branch
       or working on the source code)
