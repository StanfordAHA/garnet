import argparse
import pandas as pd
import re


def gen_power_df(filename: str, instances: list):
    power_columns = ['internal', 'switching', 'leakage', 'total']
    power_df = pd.DataFrame(0.0, index=instances, columns=power_columns)
    with open(filename, 'r') as f:
        line_start = False
        for line in f.readlines():
            if line_start is True:
                if line.startswith( '---------------------' ):
                    break
                is_counted = False
                line_list = line.split()
                cell_name = line_list[0]
                power_list = line_list[1:5]
                for inst in instances:
                    if bool(re.search(inst, cell_name)) is True:
                        power_df.loc[inst] += list(map(float, power_list))
                        is_counted = True
                        break  # inst should be included in only one index
                if is_counted is False:  # If not counted, add it to misc.
                    line_list = line.split()
                    power_df.loc['misc'] += list(map(float, power_list))
            elif line.startswith( '---------------------' ):
                line_start = True
    
    return power_df
        

def main():
    parser = argparse.ArgumentParser(description='Power Report Parser')
    parser.add_argument('--filename', '-f', type=str, default="")
    parser.add_argument('--instances', '-i', nargs='+', default=[])
    parser.add_argument('--csv', '-c', type=str, default="power_by_module.csv")
    args = parser.parse_args()

    if 'misc' not in args.instances:
        instances = args.instances + ['misc']
    power_df = gen_power_df(args.filename, instances)
    power_df.to_csv(args.csv)


if __name__ == "__main__":
    main()
