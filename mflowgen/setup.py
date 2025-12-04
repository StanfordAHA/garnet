# from distutils.core import setup  # Internet says to use this one
from setuptools import setup        # ...but this is what we've always used til now...
setup(
    name='garnet-pd',
    packages=[
        'common',
        'full_chip',
        'glb_tile',
        'glb_top',
        'global_controller',
        'tile_array',
        'Tile_MemCore',
        'Tile_PE',
    ],
    author='Alex Carsello',
    url='https://github.com/StanfordAHA/garnet/tree/master/mflowgen',
    install_requires=[
        'mflowgen'
    ],
)
