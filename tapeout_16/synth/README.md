# Raw notes

<pre>
Some say we should do our work in the /sim partition
e.g. /sim/steveri/... but, against better advice maybe,
I think I will use my home directory because:

  % df /home /sim
  Filesystem     1K-blocks      Used Available Use% Mounted on
  /dev/sdc1      786046980  11641840 774405140   2% /home
  /dev/sdd1      157208580 149838804   7369776  96% /sim





    Stephen Richardson <steveri@stanford.edu>
    To:Priyanka Raina
    Cc:Mark A. Horowitz
    Jul 24 at 4:30 PM
    Priyanka, This is Alex's original mail (below).

    You may remember that it was missing a couple of things; in particular we had to find and copy Tile_{PE,MemCore} lib and lef files into the synth directory or else the script complains that they are missing; IIRC those are found here:

    % ls /sim/ajcars/aha-arm-soc-june-2019/components/cgra/garnet/tapeout_16/synth/Tile_{PE,MemCore}/pnr.l??
    /sim/ajcars/aha-arm-soc-june-2019/components/cgra/garnet/tapeout_16/synth/Tile_MemCore/pnr.lef
    /sim/ajcars/aha-arm-soc-june-2019/components/cgra/garnet/tapeout_16/synth/Tile_MemCore/pnr.lib
    /sim/ajcars/aha-arm-soc-june-2019/components/cgra/garnet/tapeout_16/synth/Tile_PE/pnr.lef
    /sim/ajcars/aha-arm-soc-june-2019/components/cgra/garnet/tapeout_16/synth/Tile_PE/pnr.lib

    One other note; according to Mark and Alex, after you run the floorplan and start pnr, the pnr seg faults the first time. then you have to reread the floorplan dataqbase and restart and then it's okay(?)

    Good luck!
    Steve



    ----- Forwarded Message -----
    From: Alex James Carsello <ajcars@stanford.edu>
    To: Mark A Horowitz <horowitz@stanford.edu>
    Cc: Stephen E Richardson <steveri@stanford.edu>
    Sent: Monday, July 22, 2019, 11:37:25 AM PDT
    Subject: Re: Running the physical design flow

    Hi Mark,
    Unfortunately, it's a bit more manual than it should be, but it's doable. You should probably start from a full-chip post-synthesis db from Genus. I believe there should be several at /sim/ajcars/aha-arm-soc-2019/implementation/synthesis/synth/ on r7arm-aha.

    Next, you should clone the Garnet repo, if you haven't already, and checkout the tapeout branch. Copy one of the synthesized folders from the directory above (It should be called GarnetSOC_pad_frame or GarnetSOC_pad_frame_<clk freq>) to garnet/tapeout_16/synth/.

    Then, cd to the post-synthesis db (garnet/tapeout_16/synth/GarnetSOC_pad_frame.

    Open innovus by doing innovus -stylus.

    Then, once it's open, do source ../../scripts/top_flow_multi_vt.tcl.

    The scripts are written for innovus19, so be sure to have that module loaded. If you want to duplicate my environment, just look at my .cshrc on r7arm-aha.

    One known bug is that innovus seems to segfault during the early stages of placement after floorplanning is complete. However, after the segfault, I simply reloaded the floorplanned db and started from placement, and things worked from there. I wasn't able to figure out why this was happening.

    The script drops .db files after the main stages of the flow. To load these db files into an Innovus session, do read_db <db file name>

    Please let me know if you have any questions or issues. I can call if needed.

    Alex
    From: Mark A Horowitz <horowitz@stanford.edu>
    Sent: Monday, July 22, 2019 12:29 AM
    To: Alex James Carsello <ajcars@stanford.edu>
    Subject: Running the physical design flow
     

    Alex,

     

    Steve Richardson and I are going to try to run the physical design flow tomorrow to better understand how it works.  Is there a directory we can use (where things are setup) to run it?  If not, I would like to talk with you briefly about what I need to do to set it up.

     

    Thanks,

     

    Mark
</pre>
