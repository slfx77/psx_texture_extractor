import traceback
import os
import struct
import sys
import png

from PyQt5.QtWidgets import (QTableWidgetItem, QApplication, QMainWindow, QFileDialog)
from main_window_ui import Ui_MainWindow
from helpers import Printer


class Window(QMainWindow, Ui_MainWindow):
    current_dir = ""
    output_dir = ""
    current_files = []
    files_extracted = 0
    create_sub_dirs = False

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

    def inputBrowseClicked(self):
        options = QFileDialog.Options()
        dir_name = QFileDialog.getExistingDirectory(self, "Choose Directory", "", options=options)
        if dir_name:
            self.current_dir = dir_name
            self.current_files = []
            self.fileTable.setRowCount(0)
            self.getPsxFiles(dir_name)

    def filter_psx_files(self, file_list):
        return filter(lambda file: file.split('.')[-1] == 'psx' or file.split('.')[-1] == 'PSX', file_list)

    def getPsxFiles(self, dir_name):
        self.inputPath.setText(dir_name)
        dir_files = [f for f in os.listdir(dir_name) if os.path.isfile(os.path.join(dir_name, f))]
        psx_files = list(self.filter_psx_files(dir_files))
        if(len(psx_files) > 0):
            self.fileTable.setRowCount(len(psx_files))
            for row, file in enumerate(psx_files):
                self.current_files.append(file)
                self.fileTable.setItem(row, 0, QTableWidgetItem(file))
            if(self.output_dir != ""):
                self.extractButton.setEnabled(True)
        else:
            self.extractButton.setEnabled(False)

    def outputBrowseClicked(self):
        options = QFileDialog.Options()
        dir_name = QFileDialog.getExistingDirectory(self, "Choose Directory", "", options=options)
        if dir_name:
            self.output_dir = dir_name
            self.outputPath.setText(dir_name)
            if(len(self.current_files) > 0):
                self.extractButton.setEnabled(True)
            else:
                self.extractButton.setEnabled(False)

    def extractClicked(self):
        self.progressBar.setValue(0)
        for index, filename in enumerate(self.current_files):
            try:
                self.import_texlib_th2(filename, self.current_dir, index)
            except Exception as e:
                print(e)
                traceback.print_exc()
                self.fileTable.setItem(index, 2, QTableWidgetItem("ERROR"))
            self.progressBar.setValue(round(index/len(self.current_files)*100))
        self.progressBar.setValue(100)

    def createSubDirsClicked(self):
        self.create_sub_dirs = not self.create_sub_dirs

    def ps1_to_32bpp(self, color):
        r = (color) & 0x1F
        g = (color >> 5) & 0x1F
        b = (color >> 10) & 0x1F
        a = (color >> 15) & 0x1

        if(r == 31 and g == 0 and b == 31):
            # Fully transparent
            return [0, 0, 0, 0]
        else:
            return [int((r/32)*255), int((g/32)*255), int((b/32)*255), 255]

    def shiftRowRight(self, row, amount):
        shifted_right = []
        shifted_right.extend(row[amount*-4:])
        shifted_right.extend(row[0:amount*-4])
        return shifted_right

    def shiftRowsDown(self, image, amount):
        new_image = image.copy()
        for _ in range(amount):
            shifted_down = []
            shifted_down.append(new_image[-1])
            shifted_down.extend(new_image[0:-1])
            new_image = shifted_down
        return new_image

    def shiftColDown(self, image, col, amount, tex_height):
        col_to_shift = []
        col_start = col * 4
        for i in range(0, tex_height):
            col_to_shift.extend(image[i][col_start:col_start+4])
        col_shifted_up = self.shiftRowRight(col_to_shift, amount)
        new_image = []
        for i in range(0, tex_height):
            if(col != 0):
                new_image.append(image[i][0:col_start])
            else:
                new_image.append([])
            new_image[i].extend(col_shifted_up[i*4:i*4+4])
            new_image[i].extend(image[i][col_start+4:])
        return new_image

    def fixPixelData(self, tex_width, tex_height, pixels):
        initial_image = []
        for i in range(0, tex_height):
            curr_row = []
            for i in reversed(range(i*tex_width, i*tex_width+tex_width)):
                curr_row.extend(pixels[i])
            shifted_right = self.shiftRowRight(curr_row, 1)
            initial_image.append(shifted_right)
        shifted_down = self.shiftRowsDown(initial_image, 1)
        first_col_shifted = self.shiftColDown(shifted_down, 0, -1, tex_height)
        return first_col_shifted

    def writeToPng(self, filename, tex_hash, tex_width, tex_height, pixels):
        self.files_extracted += 1
        filename_without_extension = "".join(filename.split(".")[0:-1])

        if self.create_sub_dirs:
            output_dir = os.path.join(self.output_dir, filename_without_extension)
        else:
            output_dir = self.output_dir

        output_path = os.path.join(output_dir, "{}_0x{:08x}{}.png".format(filename_without_extension, tex_hash, self.files_extracted))
        converted_pixels = self.fixPixelData(tex_width, tex_height, pixels)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        file = open(output_path, 'wb')
        writer = png.Writer(tex_width, tex_height, greyscale=False, alpha=True)
        writer.write(file, converted_pixels)
        file.close()

    def import_texlib_th2(self, filename, directory, file_index):
        printer = Printer()
        printer.on = True
        input_file = os.path.join(directory, filename)
        textures_written = 0

        tex_hashes = {}
        with open(input_file, "rb") as input:
            reader = input

            # Read the file header and determine the number of objects, pointer to tagged chunks
            magic = reader.read(4)

            # Search for magic numbers, exit if not found(?)
            assert magic == b"\x04\x00\x02\x00" or magic == b"\x03\x00\x02\x00" or magic == b"\x06\x00\x02\x00"

            # Read two integers, ptr_meta, obj_count (8 bytes)
            ptr_meta, obj_count, = struct.unpack("<II", reader.read(8))

            # Initialize TEXPSX_DATA dictionary
            TEXPSX_DATA = {}

            printer("Num objects: {}", obj_count)

            # "Objects" are 36 bytes. Skip over them for reading textures.
            for i in range(obj_count):
                # Skip over object data
                reader.read(36)

            # Determine number of meshes (we need to skip over the mesh name list before texture info)
            mesh_count = struct.unpack("<I", reader.read(4))[0]
            printer("Num meshes: {}", mesh_count)

            # Skip to the tagged chunks, find the textures
            reader.seek(ptr_meta)
            chunk_count = -1
            while True:
                magic = reader.read(4)
                chunk_count += 1
                if magic != b"\xFF\xFF\xFF\xFF":
                    printer("SKIPPED CHUNK: 0x{}", magic.hex())
                    unk_length = struct.unpack("<I", reader.read(4))[0]
                    reader.read(unk_length)
                    if chunk_count > 16:
                        # There should not be this many tagged chunks, must be a file error
                        raise Exception("Unable to parse PSX texture library, cannot find texture data")
                else:
                    print("END OF TAGGED CHUNKS")
                    break

            # Now we are at the model names list - if there are any models
            for i in range(mesh_count):
                reader.read(4)

            # Print position where texture data starts
            print("we are at: {}".format(hex(reader.tell())))

            # Read number of textures
            num_tex = struct.unpack("<I", reader.read(4))[0]
            printer("Num textures: {}", num_tex)
            TEXPSX_DATA["num_tex"] = num_tex
            self.fileTable.setItem(file_index, 1, QTableWidgetItem(str(num_tex)))

            tex_names = []
            for i in range(num_tex):
                tex_names.append(struct.unpack("<I", reader.read(4))[0])
            TEXPSX_DATA["tex_names"] = tex_names

            # -------------------------------------------------
            # Direct reading from the PSX file - incomplete
            # -------------------------------------------------

            # Read 16-color palettes
            num_4bit = struct.unpack("<I", reader.read(4))[0]
            printer("Num 16-color tex: {}", num_4bit)
            palette_4bit = []
            for i in range(num_4bit):
                this_pal = {"texid": struct.unpack("<I", reader.read(4))[0]}
                this_pal["colordata"] = struct.unpack("16H", reader.read(16*2))
                palette_4bit.append(this_pal)

            # Read 256-color palettes
            num_8bit = struct.unpack("<I", reader.read(4))[0]
            printer("Num 256-color tex: {}", num_8bit)
            palette_8bit = []
            for i in range(num_8bit):
                this_pal = {"texid": struct.unpack("<I", reader.read(4))[0]}
                this_pal["colordata"] = struct.unpack("256H", reader.read(256*2))
                palette_8bit.append(this_pal)

            num_actual_tex = struct.unpack("<I", reader.read(4))[0]
            printer("Num actual textures: {}", num_actual_tex)
            # Set the number of textures for this file
            self.fileTable.setItem(file_index, 1, QTableWidgetItem(str(num_actual_tex)))
            printer("I am at: {}", hex(reader.tell()))

            for i in range(num_actual_tex):
                # Maybe THPS2 beta only? 4-byte blocks that seem meaningless
                reader.read(4)

            printer("I am at: {}", hex(reader.tell()))
            TEXPSX_DATA["texinfo"] = []
            for i in range(num_actual_tex):
                tex_unk1 = struct.unpack("<I", reader.read(4))[0]
                tex_palsize = struct.unpack("<I", reader.read(4))[0]
                tex_hash = struct.unpack("<I", reader.read(4))[0]
                tex_index = struct.unpack("<I", reader.read(4))[0]
                tex_width = struct.unpack("<H", reader.read(2))[0]
                tex_height = struct.unpack("<H", reader.read(2))[0]
                printer("{}: tex_unk1: {}, palette: {}, tex dimensions: {} {}", tex_index, tex_unk1, tex_palsize, tex_width, tex_height)
                tex_hashes[i] = tex_names[i]  # tex_hash
                TEXPSX_DATA["texinfo"].append({
                    "palette": tex_palsize, "hash": tex_hash, "index": tex_index, "width": tex_width, "height": tex_height
                })

                tex_height_is_odd = tex_height % 2 != 0

                # Now read the raw texture data
                if tex_palsize == 16:
                    pad_width = (tex_width + 0x3) & ~0x3
                    pad_width >>= 1
                    if(tex_height_is_odd):
                        extra_padding = 2 if pad_width % 4 != 0 else 0
                    else:
                        extra_padding = 0
                    real_len = (pad_width * tex_height) + extra_padding
                    pal_indices = reader.read(real_len)  # Just read for now

                    # Find the palette and build the image
                    for pal in palette_4bit:
                        if pal["texid"] == tex_hash:
                            pixels = [None] * (tex_width * tex_height)
                            for y in range(tex_height):
                                for x in range(tex_width):
                                    v = (pal_indices[y * pad_width + (x >> 1)] >> ((x & 0x1) * 4)) & 0xF
                                    color = pal["colordata"][v]
                                    pixel = self.ps1_to_32bpp(color)
                                    pixels[y * tex_width - x] = pixel
                            printer("{}: Finished reading texture. I am at: {}", tex_index, hex(reader.tell()))
                            self.writeToPng(filename, tex_hash, tex_width, tex_height, pixels)
                            textures_written += 1
                            break
                elif tex_palsize == 256:
                    pad_width = (tex_width + 0x1) & ~0x1
                    if(tex_height_is_odd):
                        extra_padding = 2 if pad_width % 4 != 0 else 0
                    else:
                        extra_padding = 0
                    real_len = (pad_width * tex_height) + extra_padding
                    pal_indices = reader.read(real_len)  # Just read for now
                    # Find the palette and build the image
                    for pal in palette_8bit:
                        if pal["texid"] == tex_hash:
                            pixels = [None] * (tex_width * tex_height)
                            for y in range(tex_height):
                                for x in range(tex_width):
                                    v = (pal_indices[y * pad_width + x]) & 0xFF
                                    color = pal["colordata"][v]
                                    pixel = self.ps1_to_32bpp(color)
                                    pixels[y * tex_width - x] = pixel
                            printer("{}: Finished reading texture. I am at: {}", tex_index, hex(reader.tell()))
                            self.writeToPng(filename, tex_hash, tex_width, tex_height, pixels)
                            textures_written += 1
                            break
            if num_actual_tex > 0:
                self.fileTable.setItem(file_index, 2, QTableWidgetItem(str(textures_written)))
                if(num_actual_tex == textures_written):
                    self.fileTable.setItem(file_index, 3, QTableWidgetItem("OK"))
                else:
                    self.fileTable.setItem(file_index, 3, QTableWidgetItem("ERROR"))
            else:
                self.fileTable.setItem(file_index, 3, QTableWidgetItem("SKIPPED"))
        print("Complete!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
