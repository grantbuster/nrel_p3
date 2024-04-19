"""
setup.py
"""
import os
from codecs import open
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.rst"), encoding="utf-8") as f:
    readme = f.read()

with open(os.path.join(here, "nrel_p3", "version.py"), encoding="utf-8") as f:
    version = f.read()

version = version.split('=')[-1].strip().strip('"').strip("'")


with open("requirements.txt") as f:
    install_requires = f.readlines()


test_requires = ["pytest>=5.2", "pytest-mock"]
description = "Energy Language Model"

setup(
    name="nrel_p3",
    version=version,
    description=description,
    long_description=readme,
    author="Grant Buster",
    author_email="grant.buster@nrel.gov",
    url="https://github.com/grantbuster/nrel_p3",
    packages=find_packages(),
    package_dir={"nrel_p3": "nrel_p3"},
    zip_safe=False,
    keywords="nrel_p3",
    python_requires='>=3.8',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    install_requires=install_requires,
)
