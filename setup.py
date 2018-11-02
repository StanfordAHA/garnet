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
        # magma/mantle not on PYPI yet, installed using requirements.txt
        # "magma",
        # "mantle",
        "coreir==0.24a",
        "bit_vector==0.34a",
        "fault==0.28",
        "delegator.py",
    ],
    python_requires='>=3.6'
)
