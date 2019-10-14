STATUS as of 10/14/2019
- pe and mem CORRECT
- top level NOT CORRECT

------------------------------------------------------------------------
See sample runs in e.g.
  /sim/steveri/tmpdir/lvs_pe
  /sim/steveri/tmpdir/lvs_mem
  /sim/steveri/tmpdir/lvs_top

------------------------------------------------------------------------
HOW-TO

# Must be on arm machine
ssh r7arm-aha

# Set up for to run calibre
module load icadv/12.30.712
module load calibre/2019.1
# etc. also see ~ajcars/.cshrc

# Find a place to work
lvs=/sim/steveri/garnet/tapeout_16/lvs/lvs.sh
mkdir /sim/$USER/tmpdir; cd /sim/$USER/tmpdir

# pe tile
cd /sim/$USER/tmpdir
mkdir lvs_pe; cd lvs_pe
top=Tile_PE
gds=/sim/steveri/garnet/tapeout_16/synth/$top/pnr.gds
vlg=/sim/steveri/garnet/tapeout_16/synth/$top/pnr.lvs.v
$lvs $gds $vlg $top |& tee lvs_pe.log

# mem tile
cd /sim/$USER/tmpdir
mkdir lvs_mem; cd lvs_mem
top=Tile_MemCore
gds=/sim/steveri/garnet/tapeout_16/synth/$top/pnr.gds
vlg=/sim/steveri/garnet/tapeout_16/synth/$top/pnr.lvs.v
$lvs $gds $vlg $top |& tee lvs_mem.log

# top
cd /sim/$USER/tmpdir
mkdir lvs_top; cd lvs_top
# You need mem/Tile_MemCore/Tile_MemCore.sp pe/Tile_PE/Tile_PE.sp
  # If you ran pe and lvs locally (above) you can just do e.g.
  ln -s lvs_pe pe; ln -s lvs_mem mem
  ln -s /sim/steveri/garnet/tapeout_16/lvs/mem .
  # Otherwise you must find and copy or link to them elsewhere
  ln -s /sim/steveri/garnet/tapeout_16/lvs/pe
  ln -s /sim/steveri/garnet/tapeout_16/lvs/mem
# Continuing...
top=GarnetSOC_pad_frame
gds=/sim/steveri/garnet/tapeout_16/synth/ref/final_final.gds
vlg=/sim/steveri/garnet/tapeout_16/synth/ref/pnr.final.lvs.v
ls -l $gds $vlg
echo $lvs $gds $vlg $top
$lvs $gds $vlg $top |& tee lvs_top.log


# See sample runs in e.g.
  /sim/steveri/tmpdir/lvs_pe
  /sim/steveri/tmpdir/lvs_mem
  /sim/steveri/tmpdir/lvs_top
