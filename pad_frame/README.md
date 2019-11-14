Don't use the pad frame in gitlab private repo.
Use this one instead.

------------------------------------------------------------------------
------------------------------------------------------------------------
This directory provides the following collateral:
  io_file
  genesis_verif/GarnetSOC_pad_frame.sv

To generate new collateral:
  % ./create_pad_frame.sh

To use pre-built collateral:
  % mkdir genesis_verif
  % cp example/genesis_verif/GarnetSOC_pad_frame.sv .
  % cp example/io_file .


NOTES:
Pad offsets can be added in the svp file e.g. see:
    //; my %pad_offset;
    //; $pad_offset{'ANAIOPAD_ext_clk_async_p'}  = 1360;
    //; $pad_offset{'ANAIOPAD_ext_Vcm'}          = 2106;
    //; $pad_offset{'IOPAD_jtag_intf_i_phy_tck'} = 3500;
    //; $pad_offset{'IOPAD_ext_dump_start'}      = 3700;
    //; $pad_offset{'IOPAD_top_VDDPST_dom3'}     = 4200;
    //; $pad_offset{'IOPAD_top_VDD_dom3'}        = 4500;


PROBLEMS: see outstanding issues filed in garnet repo (below).

------------------------------------------------------------------------
ISSUE 1 - Tapeout: Does IOPAD ordering matter?
SOLVED: No it does not matter

https://github.com/StanfordAHA/garnet/issues/375
cc: nikhil alex songjin ctorng horowitz

Generated io_file pads are in a different order than the cached version `example/io_file`:

```
% cat example/io_file
...
(iopad
	(top
                ...
		(inst name="IOPAD_ext_dump_start" offset=3700)
		(inst name="IOPAD_top_VDDPST_dom3" offset=4200)
		(inst name="IOPAD_top_VDD_dom3" offset=4500)
		(inst name="IOPAD_top_rte_dom3")
% cat io_file
...
(iopad
	(top
                ...
		(inst name="IOPAD_ext_dump_start" offset=3700)
		(inst name="IOPAD_top_VDD_dom3" offset=4500)
		(inst name="IOPAD_top_VDDPST_dom3" offset=4200)
		(inst name="IOPAD_top_rte_dom3")
```

Questions:
* is order important?
* which one is correct??


------------------------------------------------------------------------
ISSUE 2 - Tapeout: Where do IOPAD offsets come from?
SOLVED: Will embed offsets in svp file

https://github.com/StanfordAHA/garnet/issues/376
nikhil alex songjin ctorng horowitz

Cached io_file example/io_file has "offset" keywords that do not appear in generated version:

```
% diff io_file example/io_file
7c7
<               (inst name="ANAIOPAD_ext_clk_async_p")
---
>               (inst name="ANAIOPAD_ext_clk_async_p" offset=1360)
17c17
<               (inst name="ANAIOPAD_ext_Vcm")
---
>               (inst name="ANAIOPAD_ext_Vcm" offset=2106)
24c24
<               (inst name="IOPAD_jtag_intf_i_phy_tck")
---
>               (inst name="IOPAD_jtag_intf_i_phy_tck" offset=3500)
30,32c30,32
<               (inst name="IOPAD_ext_dump_start")
<               (inst name="IOPAD_top_VDD_dom3")
<               (inst name="IOPAD_top_VDDPST_dom3")
---
>               (inst name="IOPAD_ext_dump_start" offset=3700)
>               (inst name="IOPAD_top_VDDPST_dom3" offset=4200)
>               (inst name="IOPAD_top_VDD_dom3" offset=4500)
```

For now I am adding a filter to the script to manually add the offsets. *This is not the right solution.*

My questions:
* why are the offsets there?
* what is the right solution for generating the offsets?









------------------------------------------------------------------------
NOTES 11/2019

Okay so I'm told that there's nothing proprietary about the pad frame.

So I'ma copy the directory from the private/secret gitlab repo to this more public area, so all the tapeout stuff will be in one place ish.

Then. I'ma put a note in the gitlab README to use this one and not that one.

We shall see how this turns out.


NOTES 11/2019

Gitlab repo referred to above is aha-arm-soc-june-2019/components/pad_frame
on the arm7 machine look for e.g.
/sim/ajcars/aha-arm-soc-june-2019/components/pad_frame
