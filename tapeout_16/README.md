# Backend script "one-button" automatic flow (buildkite)

Buildkite runs the full Garnet physical flow on every check-in to the "tapeout_sr" branch.
The run includes two separate pipelines. One runs the generator
followed by tile synthesis and layout, and one runs the top-level PNR, e.g.
* https://buildkite.com/tapeout-aha/pe-plus-mem/builds/128
* https://buildkite.com/tapeout-aha/top/builds/326

Top-level PNR runs as six or seven separate stages running in parallel. 

Each PNR stage uses a golden database as its starting point; the
golden databases currently reside in the ARM machine directory
/sim/steveri/garnet/tapeout_16/synth/ref


# Backend script "one-button" automatic (local)

To run Garnet flow locally, you must be in a cloned garnet repo on the arm7 machine. Then

* navigate to subdirectory `tapeout_16`
* type `bin/build_local.sh --help` and follow the directions
* build_local will do most of its work in subdir `garnet/tapeout_16/synth`. In particular, the top-level physical design will take place in `garnet/tapeout_16/synth/GarnetSOC_pad_frame/`. See `/sim/steveri/garnet/tapeout_16/synth` for multiple examples of past runs.
* Because of how backups work on the arm7 machine, please don't run physical design in your home directory; instead you should have a non-backed-up `/sim/$USER` place to play...

This is what the build_local help looks like currently:

```
% bin/build_local.sh --help

Uses buildkite scripts to run synthesis and layout locally

Usage:
    # Use -v for verbose, -q for quiet execution
    bin/build_local.sh [ -v | -q ] <options>

Examples:
    # Run generator, PE and mem tile synthesis and layout, and top-level layout
    bin/build_local.sh

    # Run top-level layout only EXCLUDING final optDesign stage
    bin/build_local.sh --top_only

    # Run ONLY the pnultimate 7-hour optDesign stage (prior design db must exist in local or gold dir)
    bin/build_local.sh --opt_only

    # Quietly run all seven stages of top-level synthesis EXCEPT final optDesign
    bin/build_local.sh -q --top_only
    bin/build_local.sh -q --top_only --vto_stages="floorplan place cts fillers route eco"

    # Quietly run all seven stages of top-level synthesis including final optDesign
    bin/build_local.sh -q --top_only --vto_stages="all"
    bin/build_local.sh -q --top_only --vto_stages="floorplan place cts fillers route opt eco"
```


# Backend scripts for interactive flow

To run the physical flow interactively, follow these directions

## Garnet generator

Starting from the top-level garnet directory, follow the steps you see in .buildkite/GEN.sh:
```
  # Set up your environment
  source .buildkite/setup.sh
  bin/requirements_check.sh

  # Generate the verilog
  cd tapeout_16
  test/generate.sh

  # Copy garnet.v to live with the generated verilog
  cp garnet.v genesis_verif/garnet.sv
```

## PE and MemCore tile synthesis

Start in the top-level garnet directory. The following collateral should still exist from the "generate" step above:
* `genesis_verif/` directory containing generated verilog plus copied `garnet.sv` file
* Generated `mem_config.txt` and `mem_synth.txt` collateral files.

Follow the steps you see in .buildkite/SYN.sh:
```
    cd tapeout_16
    ln -s ../genesis_verif

    # Set up your environment
    test/module_loads.sh
    PWR_AWARE=1

    # PE synthesis / dc
    rm -rf synth/PE; cd synth/PE
    dc_shell -f ../../scripts/dc_synthesize.tcl -output_log_file dc.log
    cd ../..
    ./cutmodule.awk PE < genesis_verif/garnet.sv > genesis_verif/garnet.no_pe.sv
    mv genesis_verif/garnet.no_pe.sv genesis_verif/garnet.sv

    # PE synthesis / genus
    synthdir=synth/Tile_PE
    rm -rf $synthdir; mkdir $synthdir; cd $synthdir
    genus -legacy_ui -f ../../scripts/synthesize.tcl
    cd ../..    

    # MemCore synthesis / genus
    synthdir=synth/Tile_MemCore
    rm -rf $synthdir; mkdir $synthdir; cd $synthdir
    genus -legacy_ui -f ../../scripts/synthesize.tcl
    cd ../..    
```

## PE and MemCore tile layout (PNR)

Start in the top-level garnet directory. You should have all the collateral generated so far from the prior steps above. In particular you should have
* synth/Tile_PE/results_syn/final_area.rpt
* synth/Tile_MemCore/results_syn/final_area.rpt

Follow the steps you see in .buildkite/PNR.sh:
```
    # Setup
    cd tapeout_16
    source test/module_loads.sh
    PWR_AWARE=1

    # PNR for PE tile
    cd synth/Tile_PE
    innovus ../../scripts/layout_Tile.tcl
    cd ../..

    # PNR for MemCore tile
    cd synth/Tile_MemCore
    innovus ../../scripts/layout_Tile.tcl
    cd ../..
```

## Top-level (SoC) layout (PNR)

Start in the top-level garnet directory. You should have all the collateral generated so far from the prior steps above. In particular you should have
* synth/Tile_PE/results_syn/final_area.rpt
* synth/Tile_MemCore/results_syn/final_area.rpt

Follow the steps you see in .buildkite/TOP.sh:
```
    # Setup
    source tapeout_16/test/module_loads.sh

    # Generate pad frame
    cd pad_frame
    Genesis2.pl -parse -generate -top   Garnet_SoC_pad_frame \
                                 -input Garnet_SoC_pad_frame.svp

    # HACK ALERT
    # Pad frame is wrong, so copy the correct one from elsewhere
    cp /sim/ajcars/to_nikhil/updated_scripts/io_file .

    cd tapeout_16/synth
    mkdir GarnetSOC_pad_frame; cd GarnetSOC_pad_frame

    # Note this will take at least 20 hours to complete :)
    innovus -stylus ../../scripts/top_garnet_staged.tcl
```

# Notes

"Final" "clean" netlist from nikhil is here, according to Alex (on arm7 machine):
`/sim/ajcars/to_nikhil/synth_06_29/f1/f2`


..but no indication that optdesign was ever run...
```
  % cd /sim/ajcars/to_nikhil/synth_06_29/f1/f2
  % grep -i opt *log* | grep -i design
    [nothing]
```

...also it appears to be using a 5ns clock instead of 3.8:
```
  % egrep 'create.*cgra_clock' ./*/mmmc/modes/functional/functional.sdc
    ./cts.db/mmmc/modes/functional/functional.sdc:\
    create_clock [get_ports {pad_cgra_clk_i[0]}]  \
    -name cgra_clock -period 5.000000 -waveform {0.000000 2.500000}
    ...
```
