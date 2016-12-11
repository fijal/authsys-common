import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "authsys_common",
    version = "0.0.1",
    author = "Maciej Fijalkowski",
    author_email = "fijall@gmail.com",
    description = ("Bloc 11 common files for authsys"),
    license = "MIT",
    keywords = "bloc11 authsys",
    url = "http://packages.python.org/authsys_common",
    packages=['authsys_common'],
    long_description=read('README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
    ],
)
