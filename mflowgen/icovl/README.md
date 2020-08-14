# mflowgen pipeline for quickly evaluating ICOVL placement

You can use this pipeline to experiment with different ways to arrange
the chip's central alignment-cell grid.  There are 42 cells in the
alignment cell array, 41 of which are actual ICOVL cells, plus one DTCD cell.
Running the pipeline will tell you how many DRC errors arise from a given layout.
A single experiment should take less than ten minutes to complete.

To do an experiment, edit the "gen_fiducial_set{}" call
in "proc add_core_fiducials{}" in file<br/>
[garnet/mflowgen/common/init-fullchip/outputs/alignment-cells.tcl](../common/init-fullchip/outputs/alignment-cells.tcl).

Check in the changes and buildkite runs automatically; in the buildkite log you will see placement info e.g.
```
  @file_info CC ICOVL array bbox LL=(700,4008)
  @file_info CC ICOVL array bbox UR=(4080,4008)
  @file_info CC DTCD cells going in at x,y=(3840,3840) (forced)
  ...
  GOOD ENOUGH
  PASS
```

E.g. currently the below call builds a 6x7 array of cells near the top
of the chip, with no DRC errors related to ICOVL or DTCD placement:
```
  gen_fiducial_set [snap_to_grid 1800.00 0.09 99.99] 3600.00 cc true 5 3.0
```

Roughly translated, this places the 42 cells as follows:
* lower-left corner of array is at (x,y) = (1800,3600)
* the "5" means to place 7 cells per row, i.e. build a 6x7 array
  * yes ugh for some reason the parameter is always two less than what you want :(
* the optional "3.0" means space the cells (horizontally) 3x more than normal spacing
  * normal spacing is about 82u I think, so this places them like 246u apart

The result of doing "make drc-icovl" with this configuration should
ultimately yield this summary:
```
  ICOVL   0 errors in  0 different categories
  DTCD    0 errors in  0 different categories
```

The original spacing looked like this:
```
  # 6/2019 ORIG SPACING and layout 21x2 (21 rows x 2 columns)
  # Vertical strip of cells in the center of the chip
  # LL corner of array is at x,y = 2346.39,2700
  # (the zero at the end means 2 cells per row)
  gen_fiducial_set [snap_to_grid 2346.30 0.09 99.99] 2700.00 cc true 0
```

Interestingly, although the original spacing had no ICOVL errors
there were DTCD problems(!)
```
  % make drc-icovl
    <<<REDACTED>>>
```

# Experimental Results

`<<<REDACTED>>>`
