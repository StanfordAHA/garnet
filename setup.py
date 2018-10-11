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
        "coreir==0.26a",
        "bit_vector==0.37a",
        "fault==0.25"
    ],
    python_requires='>=3.6'
)
