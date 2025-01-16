from setuptools import setup


setup(
    name='garnet-pd',
    author='Alex Carsello',
    url='https://github.com/StanfordAHA/garnet/tree/master/mflowgen',

    install_requires = [
        'mflowgen'
    ],

    packages=['soc', 'icovl', 'common', 'Tile_PE', 'glb_top', 'glb_tile', 'full_chip', 'pad_frame', 'tile_array', 'regressions', 'Tile_MemCore', 'global_controller']

)
