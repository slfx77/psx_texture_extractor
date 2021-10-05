# Requirements

- python3
- pyqt5 - can be installed with `pip install PyQt5`

# Usage Instructions

This program can be running `py main.py` in the directory it is extracted to. Then, simply select the folder containing the psx files you wish to extract the textures from, and the folder to output the textures to. The default behavior will dump all textures in the folder of your choice. By selecting the create subdirectories button, it will create a folder for each psx file.

# Known bugs

There is no error handling at the moment for when the folder that has been selected is then deleted. The program will crash in this scenario.

# Credits

This program is essentially a wrapper around code from [io_thps_scene](https://github.com/denetii/io_thps_scene), a Blender plugin for multiple formats used in the Tony Hawk series of games as well as other games developed by Neversoft which use the same formats.
