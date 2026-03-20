from setuptools import setup


setup(
    name='garnet-pd',
    author='Alex Carsello',
    url='https://github.com/StanfordAHA/garnet/tree/master/mflowgen',

    install_requires = [
        'mflowgen'
    ],

    packages=['common', 'Tile_PE', 'glb_top', 'glb_tile', 'full_chip', 'tile_array', 'Tile_MemCore', 'global_controller', 'ProcessingElement', 'MatrixUnit']

)
