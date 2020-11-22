import subprocess
import os

def main():
    design = os.environ.get('design_name')
    f = open(f'./inputs/tiles_{design}.list', 'r')

    for line in f:
        fields = line.strip().split(',')
        x = fields[-2]
        y = fields[-1]
        tile_id = f"Tile_X{x}_Y{y}"
        os.environ["tile_id"] = tile_id
        subprocess.run(['./run.sh'])

if __name__ == '__main__':
    main()
