import glob
import shutil
import os

# scrit to copy pd files for gls sim and ptpx into netlist folder
os.makedirs('netlist', exist_ok=True)

build_folder = '/sim/ajcars/fc-4-25/'
pe_folder = '/sim/melchert/pe/'
tech = 'gf12'

design_list = ['GarnetSOC_pad_frame', 'global_controller', 'glb_top', 'glb_tile', 'tile_array', 'Tile_PE', "Tile_MemCore"]

file_type = ['*.pt.sdc', '*.vcs.v', '*.vcs.pg.v']

# signoff results folder
for ext in file_type:
    shutil.copy(glob.glob(build_folder + '/*cadence-innovus-signoff/results/'+ ext, recursive=True)[0], 'netlist/design' + ext[1:])
    shutil.copy(glob.glob(build_folder + '/*global_controller/*cadence-innovus-signoff/results/'+ ext, recursive=True)[0], 'netlist/global_controller' + ext[1:])
    shutil.copy(glob.glob(build_folder + '/*glb_top/*cadence-innovus-signoff/results/'+ ext, recursive=True)[0], 'netlist/glb_top' + ext[1:])
    shutil.copy(glob.glob(build_folder + '/*glb_top/*glb_tile/*cadence-innovus-signoff/results/'+ ext, recursive=True)[0], 'netlist/glb_tile' + ext[1:])
    shutil.copy(glob.glob(build_folder + '/*tile_array/*cadence-innovus-signoff/results/'+ ext, recursive=True)[0], 'netlist/tile_array' + ext[1:])
    shutil.copy(glob.glob(pe_folder + '/*cadence-innovus-signoff/results/'+ ext, recursive=True)[0], 'netlist/Tile_PE' + ext[1:])
    shutil.copy(glob.glob(build_folder + '/*tile_array/*Tile_MemCore/*cadence-innovus-signoff/results/'+ ext, recursive=True)[0], 'netlist/Tile_MemCore' + ext[1:])


file_type = ['*.spef.gz']

# signoff output folder
for ext in file_type:
    shutil.copy(glob.glob(build_folder + '/*cadence-innovus-signoff/outputs/'+ ext, recursive=True)[0], 'netlist/design' + ext[1:])
    shutil.copy(glob.glob(build_folder + '/*global_controller/*cadence-innovus-signoff/outputs/'+ ext, recursive=True)[0], 'netlist/global_controller' + ext[1:])
    shutil.copy(glob.glob(build_folder + '/*glb_top/*cadence-innovus-signoff/outputs/'+ ext, recursive=True)[0], 'netlist/glb_top' + ext[1:])
    shutil.copy(glob.glob(build_folder + '/*glb_top/*glb_tile/*cadence-innovus-signoff/outputs/'+ ext, recursive=True)[0], 'netlist/glb_tile' + ext[1:])
    shutil.copy(glob.glob(build_folder + '/*tile_array/*cadence-innovus-signoff/outputs/'+ ext, recursive=True)[0], 'netlist/tile_array' + ext[1:])
    shutil.copy(glob.glob(pe_folder + '/*cadence-innovus-signoff/outputs/'+ ext, recursive=True)[0], 'netlist/Tile_PE' + ext[1:])
    shutil.copy(glob.glob(build_folder + '/*tile_array/*Tile_MemCore/*cadence-innovus-signoff/outputs/'+ ext, recursive=True)[0], 'netlist/Tile_MemCore' + ext[1:])

file_type = ['stdcells-prim.v', 'stdcells-lvt.v', 'stdcells-ulvt.v', 'stdcells-pm.v', 'stdcells.db', 'stdcells-lvt.db', 'stdcells-ulvt.db', 'stdcells-pm.db']

# copy std cells
# TODO currently hardcoded for tsmc16
for ext in file_type:
    shutil.copy(glob.glob(build_folder + '/*' + tech + '*/stdcells*/'+ ext, recursive=True)[0], 'netlist/')

# mem tile and glb srams
shutil.copy(glob.glob(build_folder + '/*glb_top/*glb_tile/*gen_sram_macro/outputs/sram.v', recursive=True)[0], 'netlist/Tile_MemCore.sram.v')
shutil.copy(glob.glob(build_folder + '/*tile_array/*Tile_MemCore/*gen_sram_macro/outputs/sram.v', recursive=True)[0], 'netlist/tile_array.sram.v')
shutil.copy(glob.glob(build_folder + '/*glb_top/*glb_tile/*gen_sram_macro/outputs/sram_tt.db', recursive=True)[0], 'netlist/Tile_MemCore_sram.db')
shutil.copy(glob.glob(build_folder + '/*tile_array/*Tile_MemCore/*gen_sram_macro/outputs/sram_tt.db', recursive=True)[0], 'netlist/tile_array_sram.db')
