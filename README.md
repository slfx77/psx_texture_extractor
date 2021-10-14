# Requirements

- python3
- pyqt5 - can be installed with `pip install PyQt5`
- pypng - Included

# Usage Instructions

This program can be running `py main.py` in the directory it is extracted to. Then, simply select the folder containing the psx files you wish to extract the textures from, and the folder to output the textures to. The default behavior will dump all textures in the folder of your choice. By selecting the create subdirectories button, it will create a folder for each psx file.

# Known bugs

- There is no error handling at the moment for when the folder that has been selected is then deleted. The program will crash in this scenario.
- The program is single threaded and will freeze while extraction is ongoing.
- Not all 16-bit palettes are currently supported. As such, these textures may fail to extract.

# Credits

This program contains code from the following other projects:

- [io_thps_scene](https://github.com/denetii/io_thps_scene), a Blender plugin for multiple formats used in the Tony Hawk series of games as well as other games developed by Neversoft which use the same formats.

- [psx_extractor](https://github.com/krystalgamer/spidey-tools/tree/master/psx_extractor), an extractor intended for the PC version of Spider-Man. This is used for the decoding of PSX files with 16-bit textures. I've also created a standalone clone in Python that can be found [here](https://github.com/slfx77/psx_extract_py).

- [pypng](https://github.com/drj11/pypng), used to write 4-bit and 8-bit textures to PNG files.
