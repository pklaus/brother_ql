
### DEBUG

This document shows some ways to help debugging the package brother\_ql.
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

