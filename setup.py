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
        "magma-lang==0.1.8",
        "mantle==0.1.11",
        "cosa==0.2.8",
        "fault==0.1.1",
        "delegator.py",
    ],
    python_requires='>=3.6'
)
