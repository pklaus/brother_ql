## brother\_ql

A Python package to control Brother QL label printers.
It implements the raster language of those printers and allows you to send instruction files to your printer.
In more details, the following is possible with this package:

* Create raster language files for the Brother label printers.
  They can be created from image files or programmatically in your own Python script.
* Print raster instruction files with your Brother label printer via different backends:
    * pyusb (works cross-platform)
    * network (works cross-platform for WiFi/Ethernet-enabled printers)
    * linux\_kernel (works on Linux only; uses the /dev/usb/lp0 device handles)

The following printers are claimed to be supported (✓ means verified by the author or by contributors):

* QL-500 (✓), QL-550 (✓), QL-560, QL-570 (✓), QL-580N, QL-650TD, QL-700 (✓), QL-710W (✓), QL-720NW (✓), QL-800 (✓), QL-810W, QL-820NWB (✓), QL-1050 (✓), and QL-1060N.

The new QL-800 series can print labels with two colors (black and red) on DK-22251 labels.

Note: If your printer has an 'Editor Lite' mode, you need to disable it if you want to print via USB.
Make sure that the corresponding LED is not lit by holding the button down until it turns off.

If you're interested in printing labels using a web interface, have a look at my project
[brother\_ql\_web](https://github.com/pklaus/brother_ql_web). It makes use of the brother\_ql
package and is also written in Python.

## Why

The special feature of this package is that no printer driver is required for it to work.
This software bypasses the whole printing system including printer drivers and directly
talks to your label printer instead. This means that even though Brother doesn't offer
a driver for the Raspberry Pi (running Linux on ARM) you can print nicely using this software.
And even if there are drivers for your operating system, many programs have difficulties to set
the page sizes and margins for the labels correctly. If you want to print with high precision
(which is important for barcodes for example), you rather want to have control about every
single pixel to be printed. This is where brother\_ql comes into the game.

## Installation

brother\_ql is available from PyPI with pip:

    pip install brother_ql
    # or to upgrade to a newer release:
    pip install --upgrade brother_ql

Alternatively, you can install the latest development version from Github using:

    pip install --upgrade https://github.com/pklaus/brother_ql/archive/master.zip

This package was mainly created for use with Python 3. The essential functionality, however, will also work with Python 2: the creation of label files.

## Usage

The main user interface of this package is the command line tool `brother_ql`.

    Usage: brother_ql [OPTIONS] COMMAND [ARGS]...
    
      Command line interface for the brother_ql Python package.
    
    Options:
      -b, --backend [pyusb|network|linux_kernel]
      -m, --model [QL-500|QL-550|QL-560|QL-570|QL-580N|QL-650TD|QL-700|QL-710W|QL-720NW|QL-800|QL-810W|QL-820NWB|QL-1050|QL-1060N]
      -p, --printer PRINTER_IDENTIFIER
                                      The identifier for the printer. This could
                                      be a string like tcp://192.168.1.21:9100 for
                                      a networked printer or
                                      usb://0x04f9:0x2015/000M6Z401370 for a
                                      printer connected via USB.
      --debug
      --help                          Show this message and exit.
    
    Commands:
      analyze   interpret a binary file containing raster...
      discover  find connected label printers
      info      list available choices (for labels or models)
      print     Print a label
      send      send an instruction file to the printer

There are some global options available such as --model and --printer.
They can also be provided by environment variables (`BROTHER_QL_MODEL` and `BROTHER_QL_PRINTER`).

The global options are followed by a command such as `info` or `print`.
The most important command is the `print` command and here is its CLI signature:

    Usage: brother_ql print [OPTIONS] IMAGE [IMAGE] ...
    
      Print a label of the provided IMAGE.
    
    Options:
      -l, --label [12|29|38|50|54|62|102|17x54|17x87|23x23|29x42|29x90|39x90|39x48|52x29|62x29|62x100|102x51|102x152|d12|d24|d58]
                                      The label (size, type - die-cut or endless).
                                      Run `brother_ql info labels` for a full
                                      list including ideal pixel dimensions.
      -r, --rotate [auto|0|90|180|270]
                                      Rotate the image (counterclock-wise) by this
                                      amount of degrees.
      -t, --threshold FLOAT           The threshold value (in percent) to
                                      discriminate between black and white pixels.
      -d, --dither                    Enable dithering when converting the image
                                      to b/w. If set, --threshold is meaningless.
      -c, --compress                  Enable compression (if available with the
                                      model). Label creation can take slightly
                                      longer but the resulting instruction size is
                                      normally considerably smaller.
      --red                           Create a label to be printed on
                                      black/red/white tape (only with QL-8xx
                                      series on DK-22251 labels). You must use
                                      this option when printing on black/red tape,
                                      even when not printing red.
      --600dpi                        Print with 600x300 dpi available on some
                                      models. Provide your image as 600x600 dpi;
                                      perpendicular to the feeding the image will
                                      be resized to 300dpi.
      --lq                            Print with low quality (faster). Default is
                                      high quality.
      --no-cut / --cut                Don't cut the tape after printing the label.
      --help                          Show this message and exit.

So, printing an image file onto 62mm endless tape on a QL-710W label printer can be as easy as:

    export BROTHER_QL_PRINTER=tcp://192.168.1.21
    export BROTHER_QL_MODEL=QL-710W
    brother_ql print -l 62 my_image.png

The available label names can be listed with `brother_ql info labels`:

     Name      Printable px   Description
     12         106           12mm endless
     29         306           29mm endless
     38         413           38mm endless
     50         554           50mm endless
     54         590           54mm endless
     62         696           62mm endless
     102       1164           102mm endless
     17x54      165 x  566    17mm x 54mm die-cut
     17x87      165 x  956    17mm x 87mm die-cut
     23x23      202 x  202    23mm x 23mm die-cut
     29x42      306 x  425    29mm x 42mm die-cut
     29x90      306 x  991    29mm x 90mm die-cut
     39x90      413 x  991    38mm x 90mm die-cut
     39x48      425 x  495    39mm x 48mm die-cut
     52x29      578 x  271    52mm x 29mm die-cut
     62x29      696 x  271    62mm x 29mm die-cut
     62x100     696 x 1109    62mm x 100mm die-cut
     102x51    1164 x  526    102mm x 51mm die-cut
     102x152   1164 x 1660    102mm x 153mm die-cut
     d12         94 x   94    12mm round die-cut
     d24        236 x  236    24mm round die-cut
     d58        618 x  618    58mm round die-cut

**Pro Tip™**:
For the best results, use image files with the matching pixel dimensions. Die-cut labels have to be in the exact pixel dimensions stated above. For endless label rolls, you can provide image files with a pixel width as stated above. If you provide a file with different dimensions when creating an endless label file, it will be scaled to fit the width.

### Legacy command line tools

For a long time, this project provided multiple command line tools, such as `brother_ql_create`, `brother_ql_print`, `brother_ql_analyze`, and more.
A documentation of their usage can be found in the [LEGACY](https://github.com/pklaus/brother_ql/blob/master/LEGACY.md).

## Links

* The source code and issue tracker of this package is to be found on **Github**: [pklaus/brother\_ql](https://github.com/pklaus/brother_ql).
* The package is also to be found on **PyPI**: [brother\_ql](https://pypi.python.org/pypi/brother_ql).
* A collection of similar software projects can be found in [SIMILAR\_SOFTWARE.md](https://github.com/pklaus/brother_ql/blob/master/SIMILAR_SOFTWARE.md)
