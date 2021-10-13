import traceback
import os
import sys
import io_thps_scene_algo
import extract_psx_algo

from PyQt5.QtWidgets import (QTableWidgetItem, QApplication, QMainWindow, QFileDialog)
from main_window_ui import Ui_MainWindow
from helpers import Printer

printer = Printer()
printer.on = False
print_traceback = False


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
        if len(psx_files) > 0:
            self.fileTable.setRowCount(len(psx_files))
            for row, file in enumerate(psx_files):
                self.current_files.append(file)
                self.fileTable.setItem(row, 0, QTableWidgetItem(file))
            if self.output_dir != "":
                self.extractButton.setEnabled(True)
        else:
            self.extractButton.setEnabled(False)

    def outputBrowseClicked(self):
        options = QFileDialog.Options()
        dir_name = QFileDialog.getExistingDirectory(self, "Choose Directory", "", options=options)
        if dir_name:
            self.output_dir = dir_name
            self.outputPath.setText(dir_name)
            if len(self.current_files) > 0:
                self.extractButton.setEnabled(True)
            else:
                self.extractButton.setEnabled(False)

    def extractClicked(self):
        self.progressBar.setValue(0)
        for index, filename in enumerate(self.current_files):
            try:
                if not io_thps_scene_algo.extract_textures(self, filename, self.current_dir, index):
                    printer("{} not supported by io_thps_scene. Trying psx_extract.", filename)
                    extract_psx_algo.extract_textures(self, filename, self.current_dir, index)
            except Exception as e:
                printer("An error ocurred while trying to extract form {}. The error was: {}", filename, e)
                if print_traceback:
                    traceback.print_exc()
                self.fileTable.setItem(index, 3, QTableWidgetItem("ERROR"))
            self.progressBar.setValue(round(index/len(self.current_files)*100))
        self.progressBar.setValue(100)

    def createSubDirsClicked(self):
        self.create_sub_dirs = not self.create_sub_dirs


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
