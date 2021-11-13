import argparse


def gen_sdf_cmd(filename, num_glb_tiles, sdf_top, sdf_tile, log):
    with open(filename, "w") as f:
        top_cmd = get_sdf_string(sdf_top, 'top.dut', 'MAXIMUM', f"{log}/glb_top.sdf.log")
        f.write(top_cmd)
        for i in range(num_glb_tiles):
            tile_cmd = get_sdf_string(sdf_tile, f"top.dut.glb_tile_gen_{i}", 'MAXIMUM', f"{log}/glb_tile_{i}.sdf.log")
            f.write(tile_cmd)


def get_sdf_string(filename, scope, mtm, log):
    result = f"SDF_FILE = {filename},\n"\
             f"SCOPE = {scope},\n"\
             f"MTM_CONTROL = {mtm},\n"\
             f"LOG_FILE = {log};\n"
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SDF command file generator")
    parser.add_argument('-f', '--filename', type=str, default="sdf_cmd.cmd")
    parser.add_argument('-n', '--num-glb-tiles', type=int, default=16)
    parser.add_argument('--top', type=str, default="glb.sdf")
    parser.add_argument('--tile', type=str, default="glb_tile.sdf")
    parser.add_argument('--log', type=str, default="sdf_logs")
    args = parser.parse_args()
    gen_sdf_cmd(args.filename, args.num_glb_tiles, args.top, args.tile, args.log)

