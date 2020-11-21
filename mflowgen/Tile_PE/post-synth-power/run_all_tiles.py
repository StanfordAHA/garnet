import subprocess

def main():
    f = open('./inputs/tiles_Tile_PE.list', 'r')

    for line in f:
        fields = line.strip().split(',')
        x = fields[-2]
        y = fields[-1]
        tile_id = f"Tile_X{x}_Y{y}"
        subprocess.run(['export', f'tile_id={tile_id}', './run.sh'])

if __name__ == '__main__':
    main()
