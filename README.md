brother\_ql
===========

A Python package to control Brother QL label printers.


Installation
------------

    pip install https://github.com/pklaus/brother_ql/archive/master.zip

Usage
-----

To analyze a binary file containing Brother QL Raster commands:

    brother_ql_reader your_brother_ql_file.bin --loglevel DEBUG 2>&1 | less

