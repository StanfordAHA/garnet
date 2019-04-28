## ASIC flow:

Note: currently the flow is heavily design-specific for 
the Berkeley Craft Phase 1 chip.

0. be in bash
1. source sourceme.sh in this directory
2. add sdc and cpf files to constraints directory
3. modify Makefrag in flow directory so that VLSITOP 
   points to your <design>, and modify other inputs 
   here as needed
4. in flow directory, type `make` to run everything,
   or use TAG/FROM/TO arguments to continue an old
   run (see scripts/run_flow.tcl for targets):

    bsub make TAG=buildblahblah FROM=fplan TO=cts FLAGS="-overwrite"

   Default options are 
    FROM=syn_generic 
    TO=postroute
    FLAGS=
    TAG=build+time_suffix

   Not including "overwrite" will cause the flowtool
   to continue from where it left not, and not redo
   steps that it already completed successfully.

## DRC:

0. be in bash
1. source sourceme.sh in this directory
2. cd signoff
3. note the build directory of the run you want
   to run DRC on (there should be a FFT2Top.merge.gds
   file in the build.../dbs/postroute directory)
4. run make on your desired build:

    bsub make -j3 drc TAG=buildblahblah

## LVS:

0. be in bash
1. source sourceme.sh in this directory
2. cd signoff
3. note the build directory of the run you want
   to run LVS on (there should be a FFT2Top.lvs.v
   file in the build.../dbs/postroute directory)
4. STOP! Run DRC first (see above). After it gets
   merges and there's a FFT2Top.innovus.gds file in 
   the drcRunDir, then you may continue.
5. run make on your desired build:

    bsub make lvs TAG=buildblahblah
