import argparse
import pandas as pd


def gen_power_df(filename: str, instances: list):
    power_columns = ['internal', 'switching', 'leakage', 'total']
    power_df = pd.DataFrame(0.0, index=instances, columns=power_columns)
    with open(filename, 'r') as f:
        line_start = False
        for line in f.readlines():
            if line_start is True:
                for inst in instances:
                    if inst in line:
                        line_list = line.split()
                        power_df.loc[inst] += list(map(float, line_list[1:5]))
            elif line.startswith( '---------------------' ):
                line_start = True
    
    return power_df
        

def main():
    parser = argparse.ArgumentParser(description='Power Report Parser')
    parser.add_argument('--filename', '-f', type=str, default="")
    parser.add_argument('--instances', '-i', nargs='+', default=[])
    parser.add_argument('--csv', '-c', type=str, default="power_by_module.csv")
    args = parser.parse_args()

    power_df = gen_power_df(args.filename, args.instances)
    power_df.to_csv(args.csv)


if __name__ == "__main__":
    main()
