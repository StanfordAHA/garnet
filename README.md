[![Build Status](https://travis-ci.com/StanfordAHA/garnet.svg?branch=master)](https://travis-ci.com/StanfordAHA/garnet)
[![codecov](https://codecov.io/gh/stanfordaha/garnet/branch/master/graph/badge.svg?token=9XcZmGqxyt)](https://codecov.io/gh/stanfordaha/garnet)

The main purpose of this repo is to investigate and experiment with implementing our CGRA using new generator infrastructure. You will find in this repo: the original Genesis2 source for top level modules, functional models, and testing infrastructure. Also, you will find common generator patterns abstracted away to make designing, testing, and programming the CGRA faster.

# Usage

Once garnet is installed, you can build e.g. a 2x2 CGRA simply by doing
```
$ python garnet.py --help
$ python garnet.py --width 2 --height 2
```

For installation instructions, read on.
If you're using the Kiwi machine, see [this wiki page](https://github.com/rsetaluri/magma_cgra/wiki/Kiwi-Environment) for info on getting your python environment setup. 

# Quick Installation

We highly recommend building in a Python virtual environment. The following commands create a virtual environment, clones the garnet repo, uses pip to install dependencies, and then builds a CGRA instance with a 32x16 array dimension.

```
$ git clone git@github.com:StanfordAHA/garnet.git
$ cd garnet
$ python3.7 -m venv venv
$ source venv/bin/activate
$ pip install -U setuptools
$ pip install -r requirements.txt
$ python garnet.py --width 32 --height 16 --verilog
```

The following installation-related subsections include further directions that may be necessary.

## Install python dependencies
```
$ pip install -r requirements.txt  # install python dependencies
$ pip install pytest
# Note: If you created a virtualenv, reactivate it to load the new `pytest`
# binary into your path
# $ source venv/bin/activate
```

## Install SMT Solver
Replace `--z3` with solver of choice (e.g. `--msat` for mathsat).
```
$ pysmt-install --z3  # Agree to license
$ pysmt-install --env   # Run the commands in the output and add them to your shell configuration file, travis example below
export PYTHONPATH="/home/travis/.smt_solvers/python-bindings-3.6:${PYTHONPATH}"
export LD_LIBRARY_PATH="/home/travis/.smt_solvers/python-bindings-3.6:${LD_LIBRARY_PATH}"
❯ pysmt-install --check # Should see z3 installed and in Python's path
Installed Solvers:
  ...
  z3        True (4.6.0)
  ...
```

## Install Genesis2
You will also need Genesis2. Again, if you're on
Kiwi, see instructions in [this wiki page](https://github.com/rsetaluri/magma_cgra/wiki/Kiwi-Environment).
Otherwise, see instructions in the [Genesis2 repo](https://github.com/StanfordVLSI/Genesis2).


## Verify functionality
We can verify that everything is setup properly by running the test suite using
pytest.
```
pytest
```

# Style guide

## Version Control
All files and collateral which we want under version control should be checked into this repo. Mainly this includes core source files, scripts, light-weight docs (e.g. .md files), and config files (e.g. .xml files). Big files (e.g. PDF documents, images) should rarely be checked into this repo; Google Drive and Dropbox are much better tools for that.

### Commit Messages
We **strongly encourage** everyone to follow standard commit message protocols. See here for a great primer on commit messages: https://chris.beams.io/posts/git-commit/. TL;DR:
- Separate subject from body with a blank line
- Limit the subject line to 50 characters
- Capitalize the subject line
- Do not end the subject line with a period
- Use the imperative mood in the subject line
- Wrap the body at 72 characters
- Use the body to explain what and why vs. how

### Workflow
The basic workflow is as follows:
- Create a new feature branch for your work, e.g. `refactor-connect-box`. Push to this branch -- there should be no restrictions on this.
- When ready, initiate a [pull request](https://help.github.com/articles/about-pull-requests/) (PR)
- Once someone else has reviewed and accepted your PR, it can be merged into master.

An aside: do your best to avoid a bunch of intermediate merges into master - insteady try [rebasing](https://git-scm.com/book/en/v2/Git-Branching-Rebasing). It makes the commit history much cleaner.

## File organization
All top-level modules should go into new directories at the top-level, and should be accompanied by a test directory. For example if you have a module named `LineBuffer`, create a directory named `line_buffer/` (for all source files related to the module) and `test_line_buffer/` for all tests related to the module. In general, every new source file should be accompanied with some test (ideally `path/to/file_test.py` contains tests for source in `path/to/file.py`). Anything that you think can be shared across modules should go in `common/` with accompanying tests in `test_common/`.

Within a module's directory, we expect to have the following files (running with the LineBuffer example):
- `line_buffer/line_buffer.py` should contain the functional model for the module.
- `line_buffer/line_buffer_magma.py` should contain the magma implementation of the module (if applicable).
- `line_buffer/line_buffer_genesis2.py` should contain the Genesis2 wrapper for the module.
- `line_buffer/genesis/line_buffer.vp` should contain the Genesis2 source for the module. All other Genesis2 source needed for this module should also be in this directory (e.g. `line_buffer/genesis/sram.vp`).
- `test_line_buffer/test_line_buffer.py` should contain tests for the functional model.
- `test_line_buffer/test_regression.py` should contain tests to verify the various implementations against each other, as well as against the functional model.

For each of the files, you can organize/name functions and classes as it most makes sense for the module (keeping to pep8 standards). However, we suggest following the patterns in `cb` and `memory_core`. Keeping consistent interfaces and naming conventions will allow for automation and introspection down the road.

## Naming conventions
We follow the following naming conventions:
- All file and directory names should be in snake case, e.g. `cb.py`, `genesis_wrapper.py`, `my_dir/sub_dir`. No capital letters should appear in file or directory names.
- Function names should also be in snake case, similar to file names, e.g. `def generate_cb()`.
- Class names should be in camel case, e.g. `class CB`, `class MyUtilityKlass`. Note that for "names" which are acronyms, e.g. FPGA, CGRA, the camel case should keep capitals. E.g. the camel case of "FPGA" is "FPGA".

## Continuous Integration

Go to [https://travis-ci.com/](https://travis-ci.com/) and sign up using your
GitHub account and enable your repository.  Add the badge to your readme.

Got to [https://coveralls.io/](https://coveralls.io/) and sign up using your
GitHub account and enable your repository.  Add the badge to your readme.

Create a .travis.yml file in your repository, see [.travis.yml](./.travis.yml)
for an example.  

## Python Style
We use the [pep8](https://www.python.org/dev/peps/pep-0008/?) style guide for
Python code.  This is the coding convention used for the Python standard
library.  Note that we use the
[pycodestyle](https://pypi.org/project/pycodestyle/) package for checking
(which used to be called `pep8` but was renamed).

Our continous integration uses `pytest` to check pep8 compliance of any code
that is checked in. If a code causes a style error, it will cause a build
failure.

We suggest using a linting plugin for your editor to help you resolve pep8
issues as you edit rather than after the fact. Here are some options:
* (vim) https://github.com/vim-syntastic/syntastic
* (vim) https://github.com/w0rp/ale
* (vim) https://github.com/autozimu/LanguageClient-neovim
* (emacs) https://github.com/flycheck/flycheck
* (pycharm) https://www.jetbrains.com/pycharm/ (built-in)
* (sublime) https://github.com/SublimeLinter/SublimeLinter

## Generators
Writing generators in magma means writing Python functions that return magma
Circuits.  Strive to make a clear distinction between the two stages of the
computation. In the body of the generator function, you should compute
functions of your parameters that might be used in your definition. This is
normal Python code.  Within the body of the Circuit definition you are
generating, you should mainly be writing magma code. It is important to
separate Python and magma code as much as possible so your generator is easy to
understand.

### Operators
Prefer using operators versus explicitly instantiating and wiring up modules.
Magma overloads operators on the Bit, Bits, UInt, and SInt types, as well as
providing a standard set of operators in mantle. Using operators leads to cleaner
code that is easier to read and understand. 

Examples
```diff
- config_addr_zero = mantle.EQ(8)
- m.wire(m.uint(0, 8), config_addr_zero.I0)
- m.wire(config_addr_zero.I1, io.config_addr[24:32])
+ config_addr_zero = mantle.eq(m.uint(0, 8), io.config_addr[24:32])
```

```diff
- config_en_set_and_addr_zero = mantle.And(2, 1)
- m.wire(config_en_set_and_addr_zero.I0, io.config_en)
- m.wire(config_en_set_and_addr_zero.I1[0], config_addr_zero.O)
- 
- m.wire(config_en_set_and_addr_zero.O[0], config_cb.CE)
+ m.wire(io.config_en & config_addr_zero, config_cb.CE)
```

### Wiring
Use function calls when possible
```diff
- m.wire(io.config_en & config_addr_zero, config_cb.CE)
- m.wire(config_cb.RESET, io.reset)
- m.wire(config_cb.I, io.config_data)
+ config_cb(io.config_data, reset=io.reset, ce=io.config_en & config_addr_zero)
```

Wire outputs to inputs
```diff
- m.wire(config_cb.RESET, io.reset)
+ m.wire(io.reset, config_cb.RESET)
```

### Minimize name munging
For example, use array types and select based on index instead of generating
names with an index embedded (e.g. "in_0", "in_1", ...)

### Reuse code
If you see code being repeated across your generators, factor them into helper
functions, modules, and packages.

### Keep your functions short
Decompose your logic into helper functions so your code is more organized,
concise, readable, and maintainable.

### Document your code
Include docstrings (see
[https://www.python.org/dev/peps/pep-0257/](https://www.python.org/dev/peps/pep-0257/)
for more info) for any functions. Use inline comments where appropriate.

Include a README with setup instructions and how to use. At a baseline, refer
users to your travis script and tests for examples.

### Branching and Pull Requests
Code should be developed on a non-master branch, and pull requested into master
when ready. All requests require at least on review by a non-author.  Keep pull
requests as minimal as possible. Organize branches by features and bug fixes.

## Testing
This repository uses the [pytest](https://docs.pytest.org/en/latest/index.html)
framework.  To install, run `pip install pytest`.

We suggest consulting the [pytest
documentation](https://docs.pytest.org/en/latest/contents.html#toc) for full
documentation including installation, tutorials, and PDF documents. Here we
will cover the basic way `pytest` is used specifically for this repository.

### Assertions
The standard pattern for writing `pytest` tests is to use the Python `assert`
statement.  See [this
page](https://docs.pytest.org/en/latest/assert.html#assert) of the `pytest`
documentation for examples and information on using the `assert` statement with
`pytest`.

### Test Discovery
`pytest` uses a standard test discovery scheme to make it easy to add new
tests.  Instead of having to do any extra work like adding a test to a
configuration file containing a list of tests, all you have to do is name your
test in a certain way and place it in the right directory for `pytest` to
automatically discover it.  See [this
page](https://docs.pytest.org/en/latest/goodpractices.html#test-discovery) from
the `pytest` documentation for the test discovery scheme.

Basically, files that have the naming scheme `test_*.py` or `*_test.py` will be
considered tests. Within those files, functions with the prefix `test_` or
functions/methods with the prefix `test_` inside a class defined with the
prefix `Test` will be considered tests.

### Fault
[fault](https://github.com/leonardt/fault) is a Python package (part of the
magma ecosystem) with abstractions for testing hardware.  See the 
[README](https://github.com/leonardt/fault#fault) for example usage and links to
documentation.
