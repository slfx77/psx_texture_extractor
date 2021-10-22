# Requirements

- [python3](https://www.python.org/)
- [pyqt5](https://pypi.org/project/PyQt5/) - can be installed with `pip install PyQt5`
- [pymorton](https://github.com/trevorprater/pymorton) - can be installed with `pip install pymorton`
- [pypng](https://github.com/drj11/pypng) - Included

# Usage Instructions

This program can be running `py main.py` in the directory it is extracted to. Then, simply select the folder containing the psx files you wish to extract the textures from, and the folder to output the textures to. The default behavior will dump all textures in the folder of your choice. By selecting the create subdirectories button, it will create a folder for each psx file.

# Known bugs

- There is no error handling for IO errors. As such, these will crash the program.
- The program is single threaded and the GUI will freeze while extraction is ongoing. Progress can be checked in the console.
- Some 16-bit textures are read incorrectly and will not appear correct when exported. These are marked with an `_i` at the end of the filename.

# Credits

This program contains code from the following other projects:

- [io_thps_scene](https://github.com/denetii/io_thps_scene), a Blender plugin for multiple formats used in the Tony Hawk series of games as well as other games developed by Neversoft which use the same formats.

- [psx_extractor](https://github.com/krystalgamer/spidey-tools/tree/master/psx_extractor), an extractor intended for the PC version of Spider-Man. This is used for the decoding of PSX files with 16-bit textures. I've also created a standalone clone in Python that can be found [here](https://github.com/slfx77/psx_extract_py).

- [Rawtex](https://zenhax.com/viewtopic.php?t=7099), a multipurpose converter for raw texture files. Used to convert 16-bit textures with palette types 0x100-0x102 and 0xd01.

- [pypng](https://github.com/drj11/pypng), used to write textures to PNG files.
