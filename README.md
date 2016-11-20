## brother\_ql

A Python package to control Brother QL label printers.
It implements the raster language of those printers and allows you to send instruction files to your printer.
In more details, the following is possible with this package:

* Create raster language files for the Brother label printers.  
  These binary files contain the instructions for the printer and can be created from image files or programmatically in your own Python script.
* Print raster instruction files with your Brother label printer via different backends:
  * pyusb (works cross-platform)
  * network (works cross-platform for WiFi/Ethernet-enabled printers)
  * linux\_kernel (works on Linux only; uses the /dev/usb/lp0 device handles)

The following printers are claimed to be supported (✓ means verified by the author or by contributors):

* QL-500 (✓), QL-550, QL-560, QL-570, QL-580N, QL-650TD, QL-700 (✓), QL-710W (✓), QL-720NW (✓), QL-1050, and QL-1060N.

### Why

The special feature of this package is that no printer driver is required for it to work.
This software bypasses the whole printing system including printer drivers and directly
talks to your label printer instead. This means that even though Brother doesn't offer
a driver for the Raspberry Pi (running Linux on ARM) you can print nicely using this software.
And even if there are drivers for your operating system, many programs have difficulties to set
the page sizes and margins for the labels correctly. If you want to print with high precision
(which is important for barcodes for example), you rather want to have control about every
single pixel to be printed. This is where brother\_ql comes into the game.

### Installation

    pip install https://github.com/pklaus/brother_ql/archive/master.zip

Upgrade to the latest version using:

    pip install --upgrade https://github.com/pklaus/brother_ql/archive/master.zip

This package was mainly created for use with Python 3. The essential functionality will also work with Python 2, though: The creation of label files.

### Usage

The main user interface of this package are its command line tools.
You can also use its functionality from your own Python code (yet, there is no dedicated API documentation).
The following sections show how to use the most important CLI tools.

#### Create

The command line tool `brother_ql_create` is possibly the most important piece of software in this package.
It allows you to create a new instruction file in the label printers' raster language:

    brother_ql_create --model QL-500 ./720x300_monochrome.png > 720x300_monochrome.bin

If you want to find out about its options, just call the tool with `--help`:

    brother_ql_create --help

giving:

    usage: brother_ql_create [-h] [--model MODEL] [--label-size LABEL_SIZE]
                             [--threshold THRESHOLD] [--no-cut]
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
      --threshold THRESHOLD, -t THRESHOLD
                            The threshold value (in percent) to discriminate
                            between black and white pixels.
      --no-cut              Don't cut the tape after printing the label.
      --loglevel LOGLEVEL   Set to DEBUG for verbose debugging output to stderr.

The image argument should be a PNG/GIF/JPEG image file.
For the best results, provide it in the right pixel dimensions (suiting the chosen `--label-size`).

Some notes:

Currently, the `brother_ql_create` tool doesn't support the 600x300 dpi mode supported by some printers.
The output will always use the 300dpix300dpi mode with the *high quality preference* set.

#### Print

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

If your printer has problems printing the instructions file, it may blink its LED (green or red) depending on the model. This can have many reasons, eg.:

* The selected label doesn't match.
* End of paper.
* Unsupported opcode (wrong `--model` when using `brother_ql_create`?)

### Debugging

More info on how to debug difficult situations is to be found in the [DEBUG doc](DEBUG.md).
