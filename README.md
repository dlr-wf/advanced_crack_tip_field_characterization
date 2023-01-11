# Advanced crack tip field characterization

This repository contains the code used to generate the results of the research article
```
D. Melching, E. Breitbarth. (2023)
Advanced crack tip field characterization using conjugate work integrals. 
International Journal of Fatigue.
DOI: 10.1016/j.ijfatigue.2023.107501
```
The published article is available [here](https://doi.org/10.1016/j.ijfatigue.2023.107501).
The preprint is available on [arXiv](https://arxiv.org/).

## Abstract
*The quantitative characterisation of crack tip loads is fundamental in fracture mechanics.
Although the potential influence of higher order terms on crack growth and stability is known,
classical studies solely rely on first order stress intensity factors. We calculate higher order
Williams coefficients using an integral technique based on conjugate work integrals and study
the convergence with increasing crack tip distance. We compare the integral method to the
state-of-the-art fitting method and provide results for higher-order terms with several crack
lengths, external forces, and sizes for widely used middle tension, single-edge cracked tension,
and compact tension specimen under mode-I loading.*

## Dependencies
*  [Python 3.8.5](https://www.python.org/downloads/release/python-385/)
*  [Ansys Mechanical 2021 R2](https://www.ansys.com/): To run the simulations, we used Ansys Mechanical APDL 2021 R2.
*  [CrackPy (internal version 0.9.3)](https://github.com/dlr-wf/crackpy): The integral method and the fitting method are implemented in CrackPy. 
The scripts are based on the unpublished pre-release version 0.9.3. **Therefore, the scripts might need to be adapted to work with the published version of CrackPy.**

## Usage

The repository contains the following folders:

* `src`: contains a utility module
* `convergence_study`: contains the APDL scripts (`*.inp`) and python scripts (`*.py`) to perform the convergence study for the integral method.
* `CT`: contains the APDL and python scripts to perform the parameter study for the CT specimen.
* `MT`: contains the APDL and python scripts to perform the parameter study for the MT specimen.
* `SECT`: contains the APDL and python scripts to perform the parameter study for the SECT specimen.

In each folder, only the python scripts need to be executed. 
The APDL scripts are called by the python scripts. 
The python scripts are executed in the following order:

### 1) Simulations 
```shell
10_ansys_simulations.py
```
This script executes the APDL scripts and performs the simulations.

### 2) Crack tip field characterization

- For the integral method (INT):
```shell
11_integral_evaluation.py
```
- For the fitting method (ODM):
```shell
21_williams_fitting.py
```

These scripts calculate the Williams coefficients using the integral method and the fitting method, respectively.
The results are stored in the subfolder `txt-files`. Additionally, plots are stored in the subfolder `plots`.

### 3) Postprocessing and visulatization
The remainining python scripts produce the plots shown in the research article.
In particular, `12_plot_alpha_vs_williams.py` and `21_plot_alpha_vs_williams.py` plot the normalized Williams coefficients $a_n$ over the normalized crack length $\alpha$ for INT and ODM, respectively.
The scripts `13_plot_approx_error.py` and `22_plot_approx_error.py` plot the approximation error on the ligament in front of the crack tip for INT and ODM, respectively.