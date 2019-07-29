##### Where to run tapeout scripts (on r7arm-aha)?

<i>
SR note - Some say we should do our work in the /sim partition
e.g. /sim/steveri/... but, against better advice maybe,
I'm thinking I will use my home directory because...
</i>

<pre>
  % df /home /sim
  Filesystem     1K-blocks      Used Available Use% Mounted on
  /dev/sdc1      786046980  11641840 774405140   2% /home
  /dev/sdd1      157208580 149838804   7369776  96% /sim
</pre>

<i>If anyone knows why this is wrong please let me know! -steveri</i>

# One-Button Tapeout Instructions

Yeah, it's not really one-button (yet) but that's what we are moving toward.

For now at least, we start with the synthisized netlist and go from there. The procedure is:

<pre>
  # Build a working directory on the tapeout machine (you'll need X events)
  % ssh -X r7arm-aha
  % mkdir /sim/$USER; cd /sim/$USER

  # Optionally, you can do an "xterm" command to confirm that X events are working
  % xterm

  # Clone the garnet repo
  % git clone https://github.com/StanfordAHA/garnet

  # Copy in a full-chip post-synthesis netlist, see notes below
  % synth_src=/sim/ajcars/aha-arm-soc-2019/implementation/synthesis/synth/
  % cp -rp $synth_src/GarnetSOC_pad_frame/ garnet/tapeout_16/synth

  # Make your way to the new local synth dir
  % cd garnet/tapeout_16/synth/GarnetSOC_pad_frame/

  # You will need pnr lib and lef files in Tile_ subdirectories :(
  % mkdir Tile_PE; mkdir Tile_Memcore
  % t16synth=/sim/ajcars/aha-arm-soc-june-2019/components/cgra/garnet/tapeout_16/synth
  % cp $t16synth/Tile_PE/pnr.{lib,lef} Tile_PE
  % cp $t16synth/Tile_MemCore/pnr.{lib,lef} Tile_MemCore

  # Set up your environment to use innovus etc
  % source /cad/modules/tcl/init/sh
  % module load base
  % module load innovus

  # Note from Alex:
  #   The scripts are written for innovus19, so be sure to have that module
  #   loaded. If you want to duplicate my environment, just look at my 
  #   ~ajcars/.cshrc on r7arm-aha.

  # Open innovus by doing innovus -stylus.
  % innovus -stylus

  # once it's open, do "source ../../scripts/top_flow_multi_vt.tcl"
  innovus> source ../../scripts/top_flow_multi_vt.tcl

</pre>


More notes from Alex:

<i>
One known bug is that innovus seems to segfault during the early
stages of placement after floorplanning is complete. However, after
the segfault, I simply reloaded the floorplanned db and started from
placement, and things worked from there. I wasn't able to figure out
why this was happening.
</i>

<i>
The script drops .db files after the main stages of the flow. To load
these db files into an Innovus session, do read_db <db file name>
</i>




# Raw notes

<pre>
Some say we should do our work in the /sim partition
e.g. /sim/steveri/... but, against better advice maybe,
I think I will use my home directory because:

  % df /home /sim
  Filesystem     1K-blocks      Used Available Use% Mounted on
  /dev/sdc1      786046980  11641840 774405140   2% /home
  /dev/sdd1      157208580 149838804   7369776  96% /sim





    Stephen Richardson
    To:Priyanka Raina
    Cc:Mark A. Horowitz
    Jul 24 at 4:30 PM
    Priyanka, This is Alex's original mail (below).

    You may remember that it was missing a couple of things; in particular
    we had to find and copy Tile_{PE,MemCore} lib and lef files into the
    synth directory or else the script complains that they are missing;
    IIRC those are found here:

    % ls /sim/ajcars/aha-arm-soc-june-2019/components/cgra/garnet/tapeout_16/synth/Tile_{PE,MemCore}/pnr.l??
    /sim/ajcars/aha-arm-soc-june-2019/components/cgra/garnet/tapeout_16/synth/Tile_MemCore/pnr.lef
    /sim/ajcars/aha-arm-soc-june-2019/components/cgra/garnet/tapeout_16/synth/Tile_MemCore/pnr.lib
    /sim/ajcars/aha-arm-soc-june-2019/components/cgra/garnet/tapeout_16/synth/Tile_PE/pnr.lef
    /sim/ajcars/aha-arm-soc-june-2019/components/cgra/garnet/tapeout_16/synth/Tile_PE/pnr.lib

    One other note; according to Mark and Alex, after you run the floorplan
    and start pnr, the pnr seg faults the first time. then you have to
    reread the floorplan dataqbase and restart and then it's okay(?)

    Good luck!
    Steve



    ----- Forwarded Message -----
    From: Alex James Carsello
    To: Mark A Horowitz
    Cc: Stephen E Richardson
    Sent: Monday, July 22, 2019, 11:37:25 AM PDT
    Subject: Re: Running the physical design flow

    Hi Mark,

    Unfortunately, it's a bit more manual than it should be, but it's
    doable. You should probably start from a full-chip post-synthesis db
    from Genus. I believe there should be several at
    /sim/ajcars/aha-arm-soc-2019/implementation/synthesis/synth/ on
    r7arm-aha.

    ** [I think there's a "june" missing in the above dir name, should be
    /sim/ajcars/aha-arm-soc-june-2019/implementation/synthesis/synth/ ]

    Next, you should clone the Garnet repo, if you haven't already, and
    checkout the tapeout branch. Copy one of the synthesized folders from
    the directory above (It should be called GarnetSOC_pad_frame or
    GarnetSOC_pad_frame_<clk freq>) to garnet/tapeout_16/synth/.

    Then, cd to the post-synthesis db
    (garnet/tapeout_16/synth/GarnetSOC_pad_frame.

    Open innovus by doing innovus -stylus.

    Then, once it's open, do source ../../scripts/top_flow_multi_vt.tcl.

    The scripts are written for innovus19, so be sure to have that module
    loaded. If you want to duplicate my environment, just look at my
    .cshrc on r7arm-aha.

    One known bug is that innovus seems to segfault during the early
    stages of placement after floorplanning is complete. However, after
    the segfault, I simply reloaded the floorplanned db and started from
    placement, and things worked from there. I wasn't able to figure out
    why this was happening.

    The script drops .db files after the main stages of the flow. To load
    these db files into an Innovus session, do read_db <db file name>

    Please let me know if you have any questions or issues. I can call if
    needed.

    Alex
    From: Mark A Horowitz
    Sent: Monday, July 22, 2019 12:29 AM
    To: Alex James Carsello
    Subject: Running the physical design flow
     
    Alex,
    Steve Richardson and I are going to try to run the physical design
    flow tomorrow to better understand how it works.  Is there a
    directory we can use (where things are setup) to run it?  If not,
    I would like to talk with you briefly about what I need to do to
    set it up.
    Thanks,

    Mark
</pre>
