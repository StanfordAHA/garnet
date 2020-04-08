This directory is `$garnet/mflowgen` . From here, you can build various components of the garnet chip. E.g. to build the PE tile you would follow instructions below.

Note that you will have to be on a machine with tsmc permissions e.g. the arm7 or tsmc machines. From there, you will need access to a clone of the mflowgen repo e.g.
```
  % mkdir /sim/$USER/github; cd /sim/$USER/github
  % git clone https://github.com/cornell-brg/mflowgen.git
  % mflowgen=/sim/$USER/github/mflowgen
```
Also: In the `$mflowgen/adks` subdirectory, you will need an appropriately-named adk for the process you want to use.
```
  % mkdir $mflowgen/adks; cd $mflowgen/adks
  % git clone http://gitlab.r7arm-aha.localdomain/alexcarsello/tsmc16-adk.git tsmc16
```

Also: You should set the GARNET_HOME environment variable or the scripts may not find necessary collateral for building rtl.
```
  % export GARNET_HOME=$garnet
```

To generate CGRA rtl, you will need proper versions of python, coreir, magma, etc. Use the `requirements_check` script to verify your environment:
```
  % $garnet/bin/requirements_check.sh
    - ERROR Cannot find installed python package 'coreir>=2.0.50'
    - ERROR Cannot find installed python package 'magma-lang>=2.0.0'
    - ERROR Cannot find installed python package 'mantle>=2.0.0'
    ERROR missing packages, maybe need to do pip3 install -r requirements.txt
```

To do layout, you will need access to dc, genus, innovus etc. Use the `.buildkite/setup*.sh` script to install the correct paths. Note calibre setup installs its own path to python3 v. 3.6.6, but RTL generation requires 3.7 or better. The setup script tries to avoid this conflict.
```
  % source $garnet/.buildkite/setup.sh
  % source $garnet/.buildkite/setup-calibre.sh
```

Also: the mflowgen makefile assumes that "python" points to a python
with version number 3.7 or better. The arm7 machine default python is
python2. One way around this is to have your own environment with the
correct setup. And/or you can do something like:
```
  % mkdir bin
  % (cd bin; ln -s /usr/local/bin/python3 python)
  % export PATH=`pwd`/bin:"$PATH"
  % hash -r
```

Inside the mflowgen repo, make and inhabit a sandbox area for the build
```
  % mkdir $mflowgen/Tile_PE; cd $mflowgen/Tile_PE
```
Configure mflowgen for the tile
```
  % ../configure --design $garnet/mflowgen/Tile_PE
```
`make list` at the command prompt tells what you can do now that you're configured. E.g. if target 19 is `mentor-calibre-drc`, you should be able to build and check the tile by doing
```
  % make list
  [ it says 19 = "mentor-calibre-drc" ]
  % make 19
```

Besides `list`, the most useful generic `make` targets are
1. `make graph` to dump a nice graph picture `graph.pdf`; and
2. `make status` to check build status; and maybe
3. `make runtimes`
