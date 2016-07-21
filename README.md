## brother\_ql ##

A Python package to control Brother QL label printers.
This package basically replaces the driver because it implements
the raster language of those printers.

Here is a list of printers claimed to be supported:

QL-500, QL-550, QL-560, QL-570, QL-580N, QL-650TD, QL-700, QL-710W, QL-720NW, QL-1050, and QL-1060N.

### Installation ###

    pip install https://github.com/pklaus/brother_ql/archive/master.zip

Upgrade to the latest version using:

    pip install --upgrade https://github.com/pklaus/brother_ql/archive/master.zip

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

    brother_ql_analyse 720x300_monochrome.bin --loglevel DEBUG

This tool also has the `--help` option.

#### Printing ####

Once you have a Brother QL command file, you can send it to the printer like this:

    cat my_label.bin > /dev/usb/lp1

Or via network (if you have a LAN/WLAN enabled Brother QL):

    nc 192.168.0.23 9100 < my_label.bin
