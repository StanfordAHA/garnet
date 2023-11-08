#=================================================================#
# File: hack_lef_antenna.py
# Author: Po-Han Chen
# Usage: python hack_lef_antenna.py <lef_path> <scale_factor>
# Description: This script is used to hack the antenna rule defined
#              in the tech lef file. We saw some antenna violation
#              in M7/M8 layers after implementation. The root cause
#              could be a loose antenna rule in the tech lef file,
#              so this script tries to make the antenna rule much
#              tighter on the M7/M8 layers. Users can specify the
#              scale factor to scale down the original antenna rule. 
#=================================================================#

import sys
import os
import re

def hack_antenna_ratio_definition_in_layer(lef_str, layer='m8', scale_factor=0.8):
    # find the first occurrence of "END {layer}"
    anchor = f"END {layer}\n"
    anchor_index = lef_str.find(anchor)

    if anchor_index == -1:
        print(f"Error: anchor string: '{anchor}' not found")
        exit(1)

    # search backwards from anchor to find "Antenna definitions"
    antenna_def_index = lef_str.rfind("Antenna definitions", 0, anchor_index)

    if antenna_def_index == -1:
        print(f"Error: 'Antenna definitions' not found before '{anchor}'")
        exit(1)

    # Initialize an offset for index adjustments
    offset = 0

    # from that position, start pattern matching "ANTENNAAREARATIO <number>"
    matches = re.finditer(r"(ANTENNAAREARATIO\s+)(\d+)", lef_str[antenna_def_index:anchor_index])

    for match in matches:
        # modify the number (e.g., increment by 1)
        match_number = match.group(2)
        modified_number = int(match_number) * scale_factor
        modified_number = str(int(modified_number))

        # print information
        print(f"[hack_lef_antenna.py] Hacking ANTENNAAREARATIO on layer {layer}:", end=' ')
        print(f"{match_number} -> {modified_number} (scale={scale_factor:.2f})")

        start_idx = match.start(2) + antenna_def_index + offset
        end_idx = match.end(2) + antenna_def_index + offset

        # replace the old number with the new number in the string
        lef_str = lef_str[:start_idx] + modified_number + lef_str[end_idx:]

        # Update the offset
        # why: everytime you modified the sdc_string, the actual location
        #      of the match in the sdc_string is changed accordingly.
        offset += len(modified_number) - len(match_number)
    
    return lef_str

def main():
    # check input arguments
    if len(sys.argv) != 3:
        print("Usage: python hack_lef_antenna.py <lef_path> <scale_factor>")
        exit(1)
    else:
        lef_path = sys.argv[1]
        scale_factor = float(sys.argv[2])

    # read in the LEF file as string
    with open(lef_path, 'r') as lef_file:
        lef_str = lef_file.read()
        # create a backup of the original LEF file
        with open(lef_path + ".bak", 'w') as lef_file_bak:
            lef_file_bak.write(lef_str)

    # Perform hack on m7 and m8 layers
    lef_str = hack_antenna_ratio_definition_in_layer(lef_str=lef_str, layer='m7', scale_factor=scale_factor)
    lef_str = hack_antenna_ratio_definition_in_layer(lef_str=lef_str, layer='m8', scale_factor=scale_factor)

    # remove the old file
    if os.path.islink(lef_path):
        os.unlink(lef_path)
    else:
        print(f"[hack_lef_antenna.py] Error: {lef_path} is not a symlink")
        exit(1)
    
    # Write the file out
    with open(lef_path, "w") as f:
        f.write(lef_str)

if __name__ == "__main__":
    main()