

# 

# Machine Learning Ground State Electron Densities
## A project by S. Batzner, S. Torrisi, and J. Vandermause


## Project Overview

We present a comparative study in which we benchmark various machine learning-based regression frameworks to learning the ground-state electron energy and density of a H2 dimer and an Aluminum crystal. This extends the work of Brockherde _et al_ to the Solid State and explores the possibiliy of a potential-energy mapping across other ML frameworks.

We present our work across datasets generated in Quantum ESPRESSO and one generated from the Quantum Monte Carlo code QMCPACK. Included in this work is a library of functions and objects to assist in the automated generation and analysis of these data sets. The exposition proceeds through a series of Jupyter Notebooks, so that the results of our study are easily replicable.


## Overview of Code

Our code has the following prerequisites. To generate the data sets, you must have the following on your local machine or available on a cluster:

- Python 3.6 (with Numpy, Scipy, Matplotlib)
- Quantum ESPRESSO

We also make use of the following Python libraries for our analysis:

- Sklearn
- PyMC



Interested readers should visit the GitHub repo of our project; the 'start_here' folder includes various examples of things we

