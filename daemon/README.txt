==== GARNET DAEMON

The GarnetDaemon class enables daemon capability for a python program,
tailored specifically for our `garnet.py` chip builder. In particular, we 
can use a daemon-enabled `garnet.py` to save time when using `garnet.py`
to do PNR for multiple applications mapped onto the same Garnet build.

==== PNR USING GARNET DAEMON

Previously, PNR for an app required two stages: 1) build the (garnet)
circuit and 2) place/route the app onto the circuit. A second PNR, for
a second app, would go through the same two stages, even when/if the
garnet circuit produced is the same for both apps.

This new daemon-based PNR builds the garnet circuit just *once*, then
runs in the background, waiting to use the circuit for one or more
requesting apps to do their PNR.
```
    % aha pnr app1 --daemon launch
        => 100 sec to build garnet circuit
        =>  50 sec to do PNR for app1

    % aha pnr app2 --daemon use
        =>  0 sec to build garnet circuit (reuses prev circuit)
        => 50 sec to do PNR for app2

    % aha pnr app3 --daemon use ...
    % aha pnr app4 --daemon use ...
```

Below are before-and-after timings for our "daily" regression tests (with
after-daemon times in parens). The daemon reduces total runtime by about 
one third, from 2972 seconds (50 min) down to 2080 seconds (35 min).

Step                Total  (d)     Map  (d)    PNR   (d)    Test (d)
------------------- -----------   ---------   ----------   ---------
garnet               709  (709)
apps/pointwise       218  (215)    51  (51)    141 (138)    26  (26)
apps/pointwise       190   (99)    42  (42)    138  (47)    10  (10)
tests/ushift         204  (113)    41  (41)    139  (48)    24  (24)
tests/arith          207  (114)    41  (41)    140  (47)    26  (26)
tests/absolute       201  (110)    40  (40)    137  (46)    24  (24)
tests/scomp          222  (132)    41  (41)    157  (67)    24  (24)
tests/ucomp          223  (130)    41  (41)    159  (66)    23  (23)
tests/uminmax        205  (112)    41  (41)    138  (45)    26  (26)
tests/rom            201  (113)    41  (41)    135  (47)    25  (25)
tests/conv_1_2       197  (116)    41  (41)    130  (49)    26  (26)
tests/conv_2_1       195  (117)    41  (41)    128  (50)    26  (26)
------------------- -----------   ---------   ----------   ---------
TOTAL               2972 (2080)   461 (461)   1542 (650)   260 (260)


PNR makes use of a version of `garnet.py` enhanced with daemon
capabilities by way of the "GarnetDaemon" class in `daemon.py`.
I.e. when you do
```
    aha pnr my-app --width 28 --height 16 --daemon launch
```
the `aha pnr` wrapper does something like
```
   garnet.py --daemon launch
         --no-pd --interconnect-only
         --input-app ${app_dir}/bin/design_top.json
         --input-file ${app_dir}/bin/input${ext}
         --output-file ${app_dir}/bin/${args_app_name}.bs
         --gold-file ${app_dir}/bin/gold${ext}
         --input-broadcast-branch-factor 2
         --input-broadcast-max-leaves 16
         --rv --sparse-cgra --sparse-cgra-combined --pipeline-pnr
         --width 28 --height 16 &
```

You can use `--daemon help` to find the latest info about how to use the daemon.
```
    % garnet.py --daemon help

    DESCRIPTION:

      garnet.py can run as a daemon to save you time when generating
      bitstreams for multiple apps using the same garnet circuit. Use
      the "launch" command to build a circuit and keep state in the
      background. The "use-daemon" command reuses the background state
      to more quickly do pnr and bitstream generation.

          --daemon launch -> process args and launch a daemon
          --daemon use    -> use existing daemon to process args
          --daemon wait   -> wait for daemon to finish processing args
          --daemon kill   -> kill the daemon
          --daemon status -> print daemon status and exit
          --daemon force  -> same as kill + launch

    EXAMPLE:
        garnet.py --daemon kill
        garnet.py --width 28 --height 16 --verilog ...
        garnet.py <app1-pnr-args> --daemon launch
        garnet.py <app2-pnr-args> --daemon use
        garnet.py <app3-pnr-args> --daemon use
        garnet.py <app4-pnr-args> --daemon use
        ...
        garnet.py --daemon kill

    NOTE! 'daemon.use' width and height must match 'daemon.launch'!!!
    NOTE 2: cannot use the same daemon for verilog *and* pnr (not sure why).
```
