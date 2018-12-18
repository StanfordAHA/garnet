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
        "magma-lang==0.1.1",
        "mantle==0.1.2",
        "cosa==0.2.8",
        "fault==0.42",
        "delegator.py",
    ],
    python_requires='>=3.6'
)
