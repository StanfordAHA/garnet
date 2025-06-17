#!/usr/bin/env python3
import re
import sys
import argparse

def parse_place(place_file):
    """
    Returns a dict mapping block_id -> (x_dec, y_dec).
    Expects lines of the form:
      <inst_name>  <x>  <y>  #<block_id>
    """
    coords = {}
    with open(place_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '#' not in line:
                continue
            body, comment = line.split('#', 1)
            block_id = comment.strip()
            fields = body.split()
            if len(fields) < 3:
                continue
            try:
                x = int(fields[1])
                y = int(fields[2])
            except ValueError:
                continue
            coords[block_id] = (x, y)
    return coords

def parse_packed(packed_file):
    """
    Returns a dict mapping block_id -> set(port_name).
    Expects lines like:
      e11: (p0, PE_output_width_17_num_1)    (m5, MEM_input_width_17_num_2)
    """
    usage = {}
    pat = re.compile(r'''
        ^\s*e\d+:\s*                     # net label
        \(\s*([^,()\s]+)\s*,\s*([^)]+)\) # (id1, port1)
        \s*\(\s*([^,()\s]+)\s*,\s*([^)]+)\) # (id2, port2)
    ''', re.VERBOSE)
    with open(packed_file) as f:
        for line in f:
            m = pat.match(line)
            if not m:
                continue
            id1, port1, id2, port2 = m.groups()
            for blk, port in ((id1, port1), (id2, port2)):
                usage.setdefault(blk, set()).add(port)
    return usage

def to_hex2(n):
    """
    Return a 2-digit uppercase hex string, e.g. 0→'00', 10→'0A', 27→'1B'.
    """
    h = format(n, 'X')
    return h.zfill(2)

def infer_block_type(port_name):
    """
     - port_name startswith 'PE_'        → PE_inst0
     - port_name startswith 'PondTop'    → PondCore_inst0
     - port_name startswith 'MEM_'       → MemCore_inst0
    """
    if port_name.startswith('PE_'):
        return 'PE_inst0'
    if port_name.startswith('PondTop'):
        return 'PondCore_inst0'
    if port_name.startswith('MEM_'):
        return 'MemCore_inst0'
    return None

def parse_width(port_name):
    """
    Looks for 'width_<N>_' in the port name, returns N as int.
    Defaults to 1 if not found.
    """
    m = re.search(r'width_(\d+)', port_name)
    if m:
        return int(m.group(1))
    return 1

def main(place_file, packed_file, output_rc):
    coords = parse_place(place_file)
    usage  = parse_packed(packed_file)

    with open(output_rc, 'w') as out:
        for blk in sorted(usage.keys()):
            # only p- and m- blocks
            if not (blk.startswith('p') or blk.startswith('m')):
                continue

            if blk not in coords:
                print(f"# WARNING: no place entry for block '{blk}'", file=sys.stderr)
                continue
            x_dec, y_dec = coords[blk]
            tx = to_hex2(x_dec)
            ty = to_hex2(y_dec)
            tile = f"Tile_X{tx}_Y{ty}"

            # separate ports by type
            type_groups = {'PE': [], 'Pond': [], 'Mem': []}
            for port in sorted(usage[blk]):
                btype = infer_block_type(port)
                if btype == 'PE_inst0':
                    type_groups['PE'].append(port)
                elif btype == 'PondCore_inst0':
                    type_groups['Pond'].append(port)
                elif btype == 'MemCore_inst0':
                    type_groups['Mem'].append(port)
                else:
                    print(f"# skip unknown block type for port '{port}'", file=sys.stderr)

            # emit one group per non-empty type
            for suffix, ports in type_groups.items():
                if not ports:
                    continue
                group_name = f"{blk}_{suffix}"
                out.write(f'addGroup "{group_name}"\n')
                for port in ports:
                    width = parse_width(port)
                    msb = width - 1
                    rng = f'[{msb}:0]'
                    # instance folder depends on suffix
                    inst = {
                        'PE':       'PE_inst0',
                        'Pond':     'PondCore_inst0',
                        'Mem':      'MemCore_inst0'
                    }[suffix]
                    path = f"/top/dut/Interconnect_inst0/{tile}/{inst}/{port}{rng}"
                    out.write(f'addSignal -h 15 {path}\n')
                out.write('\n')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a Verdi signal.rc from design.place and design.packed")
    parser.add_argument("place",    help="path to design.place file")
    parser.add_argument("packed",   help="path to design.packed file")
    parser.add_argument("output_rc",help="path to write the resulting .rc file")
    args = parser.parse_args()

    main(args.place, args.packed, args.output_rc)
