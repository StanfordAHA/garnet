[![Build Status](https://travis-ci.com/StanfordAHA/garnet.svg?branch=master)](https://travis-ci.com/StanfordAHA/garnet)
[![codecov](https://codecov.io/gh/stanfordaha/garnet/branch/master/graph/badge.svg?token=9XcZmGqxyt)](https://codecov.io/gh/stanfordaha/garnet)

This repo lets you investigate and experiment with implementing our CGRA using new generator infrastructure. Here you will find: original Genesis2 source for top level modules, functional models, and testing infrastructure. Also, you will find common generator patterns abstracted away to make designing, testing, and programming the CGRA faster.

# Usage

Once garnet is installed, you can build e.g. a 2x2 CGRA simply by doing
```
$ python garnet.py --help
$ python garnet.py --width 4 --height 2
```
For installation instructions, read on.


# Install and Build (also see issue https://github.com/StanfordAHA/garnet/issues/1037)

  We use a docker environment to build the chip. Here's how:

### Use AHA repo to boot up a docker image and container
```
$ git clone https://github.com/StanfordAHA/aha aha
$ cd aha; git submodule init update --recursive
$ docker build . -t aha_image           # May need sudo depending on your setup
$ docker exec -it aha_container bash    # May need sudo depending on your setup
```

### (Inside docker now) build a 4x2 CGRA `garnet.v`
```
$ source /aha/bin/activate
$ cd /aha/garnet
$ python garnet.py --width 4 --height 2 --verilog
```


## Verify functionality
We can verify that everything is setup properly by running the test suite using
pytest.
```
$ cd /aha; ./garnet/.github/scripts/run_pytest.sh
```
(FYI last time I tried this it did not work until I first did `cd /aha/garnet; git checkout master` ...?)

# Style guide

Please read and follow the
[style guide in the AHA wiki](https://github.com/StanfordAHA/aha/wiki/Style-Guide).
