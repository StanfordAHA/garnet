This directory is `$garnet_repo/mflowgen` . From here, you can build various components of the garnet chip. E.g. to build the PE tile you would follow instructions below.

Note that you will have to be on a machine with tsmc permissions e.g. the arm7 or tsmc machines. From there, you will need access to a clone of the mflowgen repo e.g.
```
  % mkdir /sim/$USER/github; cd /sim/$USER/github
  % git clone https://github.com/cornell-brg/mflowgen.git
  % mfg_repo=/sim/$USER/github/mflowgen
```
Also: In the `$mfg_repo/adks` subdirectory, you will need an appropriately-named adk for the process you want to use.
```
  % mkdir $mfg_repo/adks; cd $mfg_repo/adks
  % git clone http://gitlab.r7arm-aha.localdomain/alexcarsello/tsmc16-adk.git
  % ln -s tsmc16-adk tsmc16
```
[ FIXME we need to make it so you don't have to rename the adk to make it work! ]

Inside the mflowgen repo, make and inhabit a sandbox area for the build
```
  % mkdir $mfg_repo/pe; cd $mfg_repo/pe
```
Configure mflowgen for the tile
```
  % ../configure --design ../../garnet/mflowgen/Tile_PE
```
`make list` at the command prompt tells what you can do now that you're configured. E.g. if target 19 is `mentor-calibre-drc`, you should be able to build and check the tile by doing
```
  % make list
  [ it says 19 = "mentor-calibre-drc"
  % make 19
```

