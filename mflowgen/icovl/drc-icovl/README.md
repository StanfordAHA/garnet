mflowgen pipeline for quickly evaluating ICOVL placement

There are 42 cells in the ICOVL array, 41 of which are actual ICOVL cells and one DTCD.


To experiment, edit the `gen_fiducial_set` call in proc
`add_core_fiducials` in file
`garnet/mflowgen/common/init-fullchip/outputs/alignment-cells.tcl`.

E.g. this builds a 6x7 array of cells near the top of the chip, with no
DRC errors related to ICOVL or DTCD placement: 
```
  gen_fiducial_set [snap_to_grid 1800.00 0.09 99.99] 3600.00 cc true 5 3.0
```

Roughly translated, this places the 42 cells as follows:
* lower-left corner of array is at (x,y) = (1800,3600)
* the "5" means to place 7 cells per row, i.e. build a 6x7 array
* yes ugh for some reason the parameter is always two less than what you want :(
* the optional "3.0" means space the cells 3x more than normal spacing
** normal spacing is about 12.6u I think, so this places them like 36u apart

The output of doing "make drc-icovl" in this pipeline should end with
this summary:
```
  ICOVL   0 errors in  0 different categories
  DTCD    0 errors in  0 different categories
```

The original spacing looked like this:
  # Vertical 2x21 strip of cells in the center of the chip
  # (the zero at the end means 2 cells per row)
  # gen_fiducial_set [snap_to_grid 2346.30 0.09 99.99] 2700.00 cc true 0

Interestingly, althought the original spacing had no ICOVL errors
there were DTCD problems(!)
```
  % make drc-icovl
    ...
    ICOVL   0 errors in  0 different categories
    DTCD  156 errors in  6 different categories
        RULECHECK DTCD.DN.4 ..................... TOTAL Result Count = 26   (26)
        RULECHECK DTCD.DN.5:TCDDMY_V2 ........... TOTAL Result Count = 26   (26)
        RULECHECK DTCD.DN.5:TCDDMY_V3 ........... TOTAL Result Count = 26   (26)
        RULECHECK DTCD.DN.5:TCDDMY_V4 ........... TOTAL Result Count = 26   (26)
        RULECHECK DTCD.DN.5:TCDDMY_V5 ........... TOTAL Result Count = 26   (26)
        RULECHECK DTCD.DN.5:TCDDMY_V6 ........... TOTAL Result Count = 26   (26)
```


Other experiments I ran include:
