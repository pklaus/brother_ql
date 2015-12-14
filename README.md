## brother\_ql ##

A Python package to control Brother QL label printers.

### Installation ###

    pip install https://github.com/pklaus/brother_ql/archive/master.zip

### Usage ###

#### Create ####

You can create a new command file to be sent to the printer with
the `brother_ql_create` tool:

    brother_ql_create --model QL-500 ./720x300_monochrome.png > 720x300_monochrome.bin

If you want to find out about its options, just call the tool with `--help`:

    brother_ql_create --help

#### Analyse ####

To analyse a binary file containing Brother QL Raster commands and
create an image of what would be printed:

    brother_ql_analyse 720x300_monochrome.bin --loglevel DEBUG 2>&1 | less

This tool also has the `--help` option.
