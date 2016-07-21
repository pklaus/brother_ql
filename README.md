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

You can create a new instruction file to be sent to the printer with
the `brother_ql_create` tool:

    brother_ql_create --model QL-500 ./720x300_monochrome.png > 720x300_monochrome.bin

If you want to find out about its options, just call the tool with `--help`:

    brother_ql_create --help

#### Analyse ####

To analyse a binary file containing Brother QL Raster instructions and
create an image of what would be printed:

    brother_ql_analyse 720x300_monochrome.bin --loglevel DEBUG

This tool also has the `--help` option.

#### Printing ####

Once you have a Brother QL instruction file, you can send it to the printer like this:

    cat my_label.bin > /dev/usb/lp1

Or via network (if you have a LAN/WLAN enabled Brother QL):

    nc 192.168.0.23 9100 < my_label.bin

You can also use the tool `brother_ql_print` to send the instructions to your printer.

    brother_ql_print 720x151_monochrome.bin usb://0x04f9:0x2015
    # or
    brother_ql_print --backend network 720x151_monochrome.bin tcp://192.168.0.23:9100
    # or
    brother_ql_print 720x151_monochrome.bin /dev/usb/lp0

#### Debugging

If your printer has problems printing the instructions file, it may blink its LED (green or red) depending on the model. This can have many reasons, eg.:

* The selected label doesn't match.
* End of paper.
* Unsupported opcode (some printers require a mode switching opcode, others fail if such an instruction is sent; some do support data compression, others don't)

To debug this situation and find out which command could be the culprit, connect your printer via USB. (You don't get any status information via network).
You can use the supplied tool `brother_ql_debug` to send your problematic instructions file to the printer. It will be split into single instructions sent one after the other.
After every instruction, the printer will be given a chance to send a status response containing error information. Here is an example:

    philipp@lion ~> brother_ql_debug ./720x151_monochrome.bin /dev/usb/lp0
    INFO: CMD preamble FOUND. Instruction: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 [...] 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 
    INFO: CMD init FOUND. Instruction: 1B 40 
    INFO: CMD status request FOUND. Instruction: 1B 69 53 
    INFO: Response from the device: 80 20 42 30 4F 30 00 00 00 00 3E 0A 00 00 15 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    INFO: Interpretation of the response: 'Reply to status request' (phase: Waiting to receive), 'Continuous length tape' 62x0 mm^2, errors: []
    INFO: CMD media/quality FOUND. Instruction: 1B 69 7A CE 0A 3E 00 97 00 00 00 01 00 
    INFO: CMD margins FOUND. Instruction: 1B 69 64 23 00 
    INFO: CMD raster FOUND. Instruction: 67 00 5A 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 FF FF FF 1F FF FF FF FF FF F0 00 00 00 00 00 0F FF FF 03 FF FF FF FF E0 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 [...] 00 07 FF FF 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 
    INFO: Response from the device: 80 20 42 30 4F 30 00 00 00 00 3E 0A 00 00 15 00 00 00 06 01 00 00 00 00 00 00 00 00 00 00 00 00
    INFO: Interpretation of the response: 'Phase change' (phase: Printing state), 'Continuous length tape' 62x0 mm^2, errors: []
    INFO: CMD print FOUND. Instruction: 1A 
    TIME 1.60
    INFO: Interpretation of the response: 'Printing completed' (phase: Printing state), 'Continuous length tape' 62x0 mm^2, errors: []
    TIME 1.60
    INFO: Interpretation of the response: 'Phase change' (phase: Waiting to receive), 'Continuous length tape' 62x0 mm^2, errors: []


To get your device supported, open a new issue on Github and paste the content of the debugging output.
