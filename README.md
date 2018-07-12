[![Build Status](https://travis-ci.com/rsetaluri/magma_connect_box.svg?branch=master)](https://travis-ci.com/rsetaluri/magma_connect_box)
[![Coverage Status](https://coveralls.io/repos/github/rsetaluri/magma_connect_box/badge.svg?branch=master)](https://coveralls.io/github/rsetaluri/magma_connect_box?branch=master)

This repository contains the files for a simple CGRA module: the connect box. In this repo you will find:
* A python functional model for the connect box ([connect_box/cb_functional_model.py](./connect_box/cb_functional_model.py))
* The original Genesis2 source for the connect box ([connect_box/cb.vp](./connect_box/cb.vp)), along with scripts to generate Verilog from the Genesis2 file (`python connect_box/cb_wrapper_main.py <args>` generates the file `genesis_verif/cb.v`)
* An implementation of the connect box in Magma
* Test harnesses to regress the Magma implementation against the original Genesis2 implementation (as well as against the functional model).

# Usage
```
pip install -r requirements.txt
pip install -e .
pytest
```

# Style guide
## Setup Continuous Integration

Go to [https://travis-ci.com/](https://travis-ci.com/) and sign up using your
GitHub account and enable your repository.  Add the badge to your readme.

Got to [https://coveralls.io/](https://coveralls.io/) and sign up using your
GitHub account and enable your repository.  Add the badge to your readme.

Create a .travis.yml file in your repository, see [.travis.yml](./.travis.yml)
for an example.  
