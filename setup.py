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
        "delegator.py",
        "coreir==0.25a",
        "bit_vector==0.34a",
        "fault==0.25"
    ],
    python_requires='>=3.6'
)
