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
        "fault==0.28",
        "delegator.py",
    ],
    python_requires='>=3.6'
)
