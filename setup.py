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
        "coreir==0.24a",
        "bit_vector==0.34a",
        "fault==0.20"
    ],
    python_requires='>=3.6'
)
