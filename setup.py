from setuptools import setup
import sys

setup(
    name='connect_box',
    version='0.1',
    description='',
    packages=[
        "connect_box",
    ],
    install_requires=[
        # magma/mantle not on PYPI yet
        # "magma",
        # "mantle",
        "coreir",
        "bit_vector"
    ],
    python_requires='>=3.6'
)
