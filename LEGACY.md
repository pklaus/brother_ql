## Legacy User Interfaces

The following user interfaces of this package are still around but their use is now deprecated and they will
be removed in a future release of the package. This documentation still lists the old UI and how it was used.

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

### DEBUG

In case of trouble printing an instruction file, there are some ways to help debugging.
One way is to look into the binary raster instruction file, see the *Analyse* section.
The other way is to send those instructions to the printer one by one and check how it reacts, see the *Debug* section.

#### Analyse

To analyse a binary file containing Brother QL Raster instructions:

    brother_ql_analyse 720x300_monochrome.bin --loglevel DEBUG

The tool will dissect your file and print the opcodes to stdout.
In addition, it creates PNG images of what the printer's output would look like.
They are saved to page0001.png etc. (yes, one .bin file can contain more than one "page").

This tool also has the `--help` option.

(This specific tool doesn't work on Python 2.)

#### Debug

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

Here, a command file was successfully printed. The last response should state the *Waiting to receive* phase.
If you want to confirm the sending of every single command individually, you can add the `--interactive` argument to the command line call.

If you're seeing any error there, open a new issue on Github containing the debugging output to get your device supported.

