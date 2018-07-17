from setuptools import setup
from codecs import open
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
        name='reco3d',
        version='0.0.0',
        description='Process 3D hit data from TPCs',
        long_description=long_description,
        author='Peter Madigan',
        author_email='pmadigan@lbl.gov',
        classifiers=[
            'Development Status :: 2 - Pre-Alpha',
            'Intended Audience :: Science/Research',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 3',
        ],
        keywords='dune physics',
        packages=['reco3d'],
        install_requires=['pytest']
)
