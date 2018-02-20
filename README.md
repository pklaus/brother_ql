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

The main user interface of this package are its command line tools.
You can also use its functionality from your own Python code (yet, there is no dedicated API documentation).
The following sections show how to use the most important CLI tools.

### Create

The command line tool `brother_ql_create` is possibly the most important piece of software in this package.
It allows you to create a new instruction file in the label printers' raster language:

    brother_ql_create --model QL-500 ./720x300_monochrome.png > 720x300_monochrome.bin

If you want to find out about its options, just call the tool with `--help`:

    brother_ql_create --help

giving:

    usage: brother_ql_create [-h] [--model MODEL] [--label-size LABEL_SIZE]
                             [--rotate {0,90,180,270}] [--threshold THRESHOLD]
                             [--dither] [--compress] [--red] [--600dpi] [--no-cut]
                             [--loglevel LOGLEVEL]
                             image [outfile]
    
    positional arguments:
      image                 The image file to create a label from.
      outfile               The file to write the instructions to. Defaults to
                            stdout.
    
    optional arguments:
      -h, --help            show this help message and exit
      --model MODEL, -m MODEL
                            The printer model to use. Check available ones with
                            `brother_ql_info list-models`.
      --label-size LABEL_SIZE, -s LABEL_SIZE
                            The label size (and kind) to use. Check available ones
                            with `brother_ql_info list-label-sizes`.
      --rotate {0,90,180,270}, -r {0,90,180,270}
                            Rotate the image (counterclock-wise) by this amount of
                            degrees.
      --threshold THRESHOLD, -t THRESHOLD
                            The threshold value (in percent) to discriminate
                            between black and white pixels.
      --dither, -d          Enable dithering when converting the image to b/w. If
                            set, --threshold is meaningless.
      --compress, -c        Enable compression (if available with the model).
                            Takes more time but results in smaller file size.
      --red                 Create a label to be printed on black/red/white tape
                            (only with QL-8xx series on DK-22251 labels). You must
                            use this option when printing on black/red tape, even
                            when not printing red.
      --600dpi              Print with 600x300 dpi available on some models.
                            Provide your image as 600x600 dpi; perpendicular to
                            the feeding the image will be resized to 300dpi.
      --no-cut              Don't cut the tape after printing the label.
      --loglevel LOGLEVEL   Set to DEBUG for verbose debugging output to stderr.

The image argument should be a PNG/GIF/JPEG image file.
Here is the output of `brother_ql_info list-label-sizes` listing the available options for `--label-size`:

    Supported label sizes:
     Name      Printable px   Description
     12         106           (12 mm endless)
     29         306           (29 mm endless)
     38         413           (38 mm endless)
     50         554           (50 mm endless)
     54         590           (54 mm endless)
     62         696           (62 mm endless)
     102       1164           (102 mm endless)
     17x54      165 x  566    (17 x 54 mm^2)
     17x87      165 x  956    (17 x 87 mm^2)
     23x23      202 x  202    (23 x 23 mm^2)
     29x42      306 x  425    (29 x 42 mm^2)
     29x90      306 x  991    (29 x 90 mm^2)
     39x90      413 x  991    (38 x 90 mm^2)
     39x48      425 x  495    (39 x 48 mm^2)
     52x29      578 x  271    (52 x 29 mm^2)
     62x29      696 x  271    (62 x 29 mm^2)
     62x100     696 x 1109    (62 x 100 mm^2)
     102x51    1164 x  526    (102 x 51 mm^2)
     102x152   1164 x 1660    (102 x 152 mm^2)
     d12         94 x   94    (12 mm diameter, round)
     d24        236 x  236    (24 mm diameter, round)
     d58        618 x  618    (58 mm diameter, round)

**Pro Tip™**:
For the best results, use image files with the matching pixel dimensions. Die-cut labels have to be in the exact pixel dimensions stated above. For endless label rolls, you can provide image files with a pixel width as stated above. If you provide a file with different dimensions when creating an endless label file, it will be scaled to fit the width.

### Print

Once you have a Brother QL instruction file, you can send it to the printer like this:

    cat my_label.bin > /dev/usb/lp1

Be sure to have permission to write to the device (usually adding yourself to the *lp* group is sufficient.

Or via network (if you have a LAN/WLAN enabled Brother QL):

    nc 192.168.0.23 9100 < my_label.bin

You can also use the tool `brother_ql_print` (Py3 only) to send the instructions to your printer:

    brother_ql_print 720x151_monochrome.bin /dev/usb/lp0
    # or
    brother_ql_print --backend network 720x151_monochrome.bin tcp://192.168.0.23:9100
    # or (requires PyUSB: `pip install pyusb`)
    brother_ql_print 720x151_monochrome.bin usb://0x04f9:0x2015
    # or if you have multiple ones connected:
    brother_ql_print 720x151_monochrome.bin usb://0x04f9:0x2015/000M6Z401370
    # where 000M6Z401370 is the serial number (see lsusb output).

If your printer has problems printing the instructions file, it may blink its LED (green or red) depending on the model. This can have many reasons, eg.:

* The selected label doesn't match (make sure `--red` has been passed to `brother_ql_create` if you're using black/red labels).
* End of paper.
* Unsupported opcode (wrong `--model` when using `brother_ql_create`?)

## Debugging

More info on how to debug difficult situations is to be found in the [DEBUG doc](https://github.com/pklaus/brother_ql/blob/master/DEBUG.md).

## Links

* The source code and issue tracker of this package is to be found on **Github**: [pklaus/brother\_ql](https://github.com/pklaus/brother_ql).
* The package is also to be found on **PyPI**: [brother\_ql](https://pypi.python.org/pypi/brother_ql).
* A collection of similar software projects can be found in [SIMILAR\_SOFTWARE.md](https://github.com/pklaus/brother_ql/blob/master/SIMILAR_SOFTWARE.md)
