#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import with_statement
from setuptools import setup, find_packages


def get_long_description():
    with open("README.md") as f:
        return f.read()


setup(
    name="msikeyboard",
    version="0.1.1",
    description="Support library and daemon for SteelSeries keyboards on MSI laptops",
    long_description=get_long_description(),
    author="DeD MorozZz",
    author_email="morozzz.g2@gmail.com",
    maintainer="DeD MorozZz",
    maintainer_email="morozzz.g2@gmail.com",
    url="https://github.com/m0r0zzz/msikeyboard",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Development Status :: 3 - Alpha",
        "Environment :: No Input/Output (Daemon)",
        "Intended Audience :: End Users/Desktop",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3"
    ],
    license = "GPL-3.0", 
    keywords = "MSI keyboard steelseries backlight", 
    packages=find_packages(),
    data_files = [("/etc/msikeyboard/",  ["data/config.yaml"])], 
    entry_points = {
        'console_scripts': ['msikeyboardd=msikeyboard.msikblightd:main'], 
    }, 
    install_requires = [
        "hidapi-cffi", 
        "dbus-python", 
        "pyyaml", 
        "pygobject"
    ]
)
