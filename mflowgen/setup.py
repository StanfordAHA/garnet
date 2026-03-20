# Sometime around Dec. 2026 the old setup, which did not explicitly enumerate
# packages, stopped working; so now I am adding the new "packages=[..." part.

# from distutils.core import setup  # Internet says to use this one
from setuptools import setup        # ...but this is what we've always used til now...
setup(
    name='garnet-pd',
    author='Alex Carsello',
    url='https://github.com/StanfordAHA/garnet/tree/master/mflowgen',
    install_requires=['mflowgen'],
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
)
