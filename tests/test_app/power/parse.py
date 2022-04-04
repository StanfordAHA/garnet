import sys
import os
from tabulate import tabulate
import argparse

def parse_fields(line):
    breakdown = line.split()
    field_map = {
                 'name': 0,
                 'module': 1,
                 'int_power': 2,
                 'switch_power': 3,
                 'leak_power': 4,
                 'total_power': 5,
                 'percentage': 6
                }
                
    if len(breakdown) < len(field_map):
        return {}
    
    fields = {}
    for i,(k,v) in enumerate(field_map.items()):
        if breakdown[v] == 'N/A':
            breakdown[v] = '0'
        fields[k] = breakdown[v]
    
    return fields
    
def process_line(line):
    level = (len(line) - len(line.lstrip())) / 2
    fields = parse_fields(line)
    if len(fields) == 0:
       return None, None 

    return level, fields
    
def peek_line(p):
    pos = p.tell()
    line = p.readline()
    p.seek(pos)
    return line
    
def parse_tile_array(filename):
    p = open(filename, 'r')
    
    while True:
        line = p.readline()
        if not line:
            break
        if line.find('Interconnect_inst0') != -1:
            break

    tile_overall = line.split()
    total_power = float(tile_overall[-2])

    curr_core = ''
    curr_name = ''
    power_breakdown = {
                       'switch_box': 0.0,
                       'connection_box': 0.0,
                       'mem': 0.0,
                       'pe': 0.0,
                       'other': total_power
                      }
    power_by_tile = {}
    while True:
        line = p.readline()
        if not line:
            break
        
        if "global_buffer" in line:
            break

        level, fields = process_line(line)
        if level is None or fields is None:
            break

        if level == 5:
            if fields['module'] == '(Tile_PE)':
                curr_core = 'pe'
            else:
                curr_core = 'mem'
            curr_name = fields['name']
            power_by_tile[curr_name] = {
                        'switch_box': 0.0,
                        'connection_box': 0.0,
                        'mem': 0.0,
                        'pe': 0.0,
                        'other': float(fields['total_power'])
                    }
        elif level == 6:
            component_power = float(fields['total_power'])
            # switch box
            if 'SB' in fields['name']:
                module = 'switch_box'
            # connection box
            elif 'CB' in fields['name']:
                module = 'connection_box'
            # core
            elif 'PE_inst0' == fields['name'] or 'MemCore_inst0' == fields['name']:
                module = curr_core
            # other things
            else:
                module = 'other'

            if module != 'other':
                power_by_tile[curr_name][module] += component_power
                power_by_tile[curr_name]['other'] -= component_power

                power_breakdown[module] += component_power
                power_breakdown['other'] -= component_power
                
    # print power numbers
    power_summary = open(f'{filename.split(".")[0]}.summary', 'w')
    headers = ['Tile', 'SB (W)', 'CB (W)', 'Mem (W)', 'PE (W)', 'Other (W)']
    data = []
    for k in sorted(power_by_tile.items()):
        k2 = {key: f'{v:.3e}' if k[1][key] != 0 else '' for key,v in k[1].items()}
        sb = k2['switch_box']
        cb = k2['connection_box']
        mem = k2['mem']
        pe = k2['pe']
        other = k2['other']
        data.append([k[0], sb, cb, mem, pe, other])
    data.append(['' for i in range(len(headers))])
    data.append(['TOTAL', f'{power_breakdown["switch_box"]:.3e}', f'{power_breakdown["connection_box"]:.3e}', f'{power_breakdown["mem"]:.3e}', f'{power_breakdown["pe"]:.3e}', f'{power_breakdown["other"]:.3e}'])
    power_summary.write(tabulate(data, headers=headers,tablefmt='plain'))

    p.close()
    power_summary.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', type=str, default='')
    args = parser.parse_args()

    parse_tile_array(args.file)

if __name__ == '__main__':
    main()