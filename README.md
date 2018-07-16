[![Build Status](https://travis-ci.com/rsetaluri/magma_cgra.svg?branch=master)](https://travis-ci.com/rsetaluri/magma_cgra)
[![Coverage Status](https://coveralls.io/repos/github/rsetaluri/magma_cgra/badge.svg?branch=master)](https://coveralls.io/github/rsetaluri/magma_cgra?branch=master)

The main purpose of this repo is to investigate and experiment with implementing our CGRA using new generator infrastructure. You will find in this repo: the original Genesis2 source for top level modules, functional models, and testing infrastructure. Also, you will find common generator patterns abstracted away to make designing, testing, and programming the CGRA faster.

# Usage
If you're using the Kiwi machine, see [this wiki page](https://github.com/rsetaluri/magma_cgra/wiki/Kiwi-Environment) for info on getting your python environment setup. If you use the shared Python environment, you do not need to run the pip install command.
```
pip install -r requirements.txt  # install python dependencies
pytest                           # install with pip install pytest 
```

# Style guide

## File organization
All top-level modules should go into new directories at the top-level, and should be accompanied by a test directory. For example if you have a module named `LineBuffer`, create a directory named `line_buffer/` (for all source files related to the module) and `test_line_buffer/` for all tests related to the module. In general, every new source file should be accompanied with some test (ideally `path/to/file_test.py` contains tests for source in `path/to/file.py`). Anything that you think can be shared across modules should go in `common/` with accompanying tests in `test_common/`.

Within a module's directory, we expect to have the following files (running with the LineBuffer example):
- `line_buffer/line_buffer.py` should contain the functional model for the module.
- `line_buffer/line_buffer_magma.py` should contain the magma implementation of the module (if applicable).
- `line_buffer/line_buffer_genesis2.py` should contain the Genesis2 wrapper for the module.
- `line_buffer/genesis/line_buffer.vp` should contain the Genesis2 source for the module. All other Genesis2 source needed for this module should also be in this directory (e.g. `line_buffer/genesis/sram.vp`).
- `test_line_buffer/test_line_buffer.py` should contain tests for the functional model.
- `test_line_buffer/test_regression.py` should contain tests to verify the various implementations against each other, as well as against the functional model.

For each of the files, you can organize/name functions and classes as it most makes sense for the module (keeping to pep8 standards). However, we suggest following the patterns in `cb` and `mem`. Keeping consistent interfaces and naming conventions will allow for automation and introspection down the road.

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
library.  

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
