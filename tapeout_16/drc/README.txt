See sample runs in e.g.
  /sim/steveri/tmpdir/drc_pe
  /sim/steveri/tmpdir/drc_mem

# Must be on arm machine
ssh r7arm-aha

# Set up for to run calibre
module load icadv/12.30.712
module load calibre/2019.1
# etc. also see ~ajcars/.cshrc

# Find a place to work
drc=/sim/steveri/garnet/tapeout_16/drc/drc.sh
mkdir /sim/$USER/tmpdir; cd /sim/$USER/tmpdir

# pe tile
cd /sim/$USER/tmpdir
mkdir drc_pe; cd drc_pe
top=Tile_PE
gds=/sim/steveri/garnet/tapeout_16/synth/$top/pnr.gds
$drc $gds $top -nofullchip -noantenna |& tee drc_pe.log

# mem tile
cd /sim/$USER/tmpdir
mkdir drc_mem; cd drc_mem
top=Tile_MemCore
gds=/sim/steveri/garnet/tapeout_16/synth/$top/pnr.gds
$drc $gds $top -nofullchip -noantenna |& tee drc_mem.log

See sample runs in e.g.
  /sim/steveri/tmpdir/drc_pe
  /sim/steveri/tmpdir/drc_mem
