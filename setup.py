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
        "magma-lang==0.1.10",
        "mantle==0.1.13",
        "cosa==0.2.8",
        "fault==1.0.3",
        "delegator.py",
    ],
    python_requires='>=3.6'
)
