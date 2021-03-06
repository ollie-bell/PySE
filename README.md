# Python Stencil Environment

All credit to http://pyfdm.sourceforge.net/ https://sourceforge.net/projects/pyfdm/
This is a fork uploaded for personal use.

Original README left in as below.

#

This is the 0.3.1 release of PySE. 

The official name will from now be:

PySE - Python Stencil Environment.

The word 'PyFDM' will be reserved for a more complete FDM tool that may appear
in the future.

The setup.py in the toplevel directory can be used to build and install
everything. The two required modules, DegMatSparse and pyfdm/clib will be
build automatically. There are separate setup.py files in those directories if
you want to build the extensions manually. 

Due to historical reasons, some of the required modules live in a separta
namespace, pyPDE. These modules are also installed by the setup script.

Required software:
==================

Given version numbers are those we have actually tested. The software may work
with earlier releases.

Numeric    >= v. 23.8
numarray   >= v. 1.3
pypar      >= v. 1.9.2. Pypar can be downloaded from 
              <url:http://datamining.anu.edu.au/~ole/pypar>
gnuplot    >= v. 4.0
gnuplot-py >= v. 1.7. Python gnuplot bindings, can be downloaded from
              <url:http://gnuplot-py.sourceforge.net>
swig       >= v. 1.3.25 - required to build DegMatSparse

Installation:
=============

Installation should be done with:

python setup.py install [--prefix=/I/want/it/here]

The installation assumes that your C++ compiler is 'g++'. If you need to use
another compiler, specify in the CXX environment variable:

export CXX=i++

The compiler is used to create extension modules for Python, so a compiler
suitable to compile dynamic loadable modules for Python must be specified.

Remark: If the DegMatSparse library is installed manually, the user must first
issue 'python setup.py build', then 'python setup.py install' in order to get
the options for swig correct.

Basic usage:
============

from pyFDM import *

User documentation will be added later on.

There are some examples in the examples subdirectory.

TODO list:

 * remove some unnecessary dependencies
 * add plotting capabilities in the packages (now: external, or rather
   internal) - some work has been done, the plotting capabilities are now
   included in the released files. But this should be improved.
 * Add documentation.

 On the mathematical side:
 
 * Add support for nonlinear problems
 * Add support for higher order methods
 * Add support for more complex geometry
 * Interface linear solver packages.

Asmund Odegard (aa at simula dot no),
Simula Research Laboratory AS
