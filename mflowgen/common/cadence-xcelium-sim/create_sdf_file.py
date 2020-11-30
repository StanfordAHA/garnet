if __name__ == "__main__":
    print("Creating sdf command file...")
    tiles = ["Tile_PE", "Tile_MemCore"]
    # We can create one file to contain all annotation commands
    with open("sub_cmd.cmd", "w+") as fi:
        for tile in tiles:
            # Read through each tile instance and annotate
            with open(f"sdf_{tile}.list", "r") as ti_fi:
                tile_coords = ti_fi.readlines()
                for tile_coord in tile_coords:
                    # Trim the newline
                    tile_coord = tile_coord.strip()
                    # Cadence format for specifying annotation of a particular design
                    new_constraint = f"SDF_FILE = \"./inputs/{tile}.sdf\",\nSCOPE = Interconnect_tb.dut.{tile_coord},\nLOG_FILE = \"./sdf_logs/{tile}_{tile_coord}_sdf.log\",\nMTM_CONTROL = \"MAXIMUM\";\n\n"
                    fi.write(new_constraint)

