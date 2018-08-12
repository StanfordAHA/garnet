from setuptools import setup
import sys

setup(
    name='cb',
    version='0.1',
    description='',
    packages=[
        "cb",
        "sb",
    ],
    install_requires=[
        # magma/mantle not on PYPI yet
        # "magma",
        # "mantle",
        "coreir",
        "bit_vector",
        "fault==0.17"
    ],
    python_requires='>=3.6'
)
