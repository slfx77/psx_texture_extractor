import os
import sys
import traceback

from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QTableWidgetItem

from helpers import Printer
from io_thps_scene import extract_textures
from main_window_ui import Ui_main_window

printer = Printer()
printer.on = True
print_traceback = True


class Window(QMainWindow, Ui_main_window):
    current_dir = ""
    output_dir = ""
    current_files = []
    files_extracted = 0
    create_sub_dirs = False

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

    def input_browse_clicked(self):
        options = QFileDialog.Options()
        dir_name = QFileDialog.getExistingDirectory(self, "Choose Directory", "", options=options)
        if dir_name:
            self.current_dir = dir_name
            self.current_files = []
            self.file_table.setRowCount(0)
            self.get_psx_files(dir_name)

    def filter_psx_files(self, file_list):
        return filter(lambda file: file.split(".")[-1] == "psx" or file.split(".")[-1] == "PSX", file_list)

    def get_psx_files(self, dir_name):
        self.input_path.setText(dir_name)
        dir_files = [f for f in os.listdir(dir_name) if os.path.isfile(os.path.join(dir_name, f))]
        psx_files = list(self.filter_psx_files(dir_files))
        if len(psx_files) > 0:
            self.file_table.setRowCount(len(psx_files))
            for row, file in enumerate(psx_files):
                self.current_files.append(file)
                self.file_table.setItem(row, 0, QTableWidgetItem(file))
            if self.output_dir != "":
                self.extract_button.setEnabled(True)
        else:
            self.extract_button.setEnabled(False)

    def output_browse_clicked(self):
        options = QFileDialog.Options()
        dir_name = QFileDialog.getExistingDirectory(self, "Choose Directory", "", options=options)
        if dir_name:
            self.output_dir = dir_name
            self.output_path.setText(dir_name)
            if len(self.current_files) > 0:
                self.extract_button.setEnabled(True)
            else:
                self.extract_button.setEnabled(False)

    def extract_clicked(self):
        self.progress_bar.setValue(0)
        self.extract_button.setEnabled(False)
        self.worker = Worker(self.current_files, self.current_dir, self.output_dir, self.file_table, self.files_extracted, self.create_sub_dirs)
        self.worker.progress_signal.connect(self.update_progress_bar)
        self.worker.extraction_complete_signal.connect(self.extraction_complete)
        self.worker.update_file_table_signal.connect(self.update_file_table)
        self.worker.file_extracted_signal.connect(self.increment_files_extracted)
        self.worker.start()

    @pyqtSlot(int)
    def update_progress_bar(self, index):
        progress = round(index / len(self.current_files) * 100)
        self.progress_bar.setValue(progress)

    @pyqtSlot(int, int, str)
    def update_file_table(self, row, col, text):
        new_item = QTableWidgetItem(text)
        self.file_table.setItem(row, col, new_item)

    @pyqtSlot()
    def increment_files_extracted(self):
        self.files_extracted += 1

    def extraction_complete(self):
        self.progress_bar.setValue(100)
        self.extract_button.setEnabled(True)

    def create_sub_dirs_clicked(self):
        self.create_sub_dirs = not self.create_sub_dirs


class Worker(QThread):
    progress_signal = pyqtSignal(int)
    extraction_complete_signal = pyqtSignal()
    update_file_table_signal = pyqtSignal(int, int, str)
    file_extracted_signal = pyqtSignal()

    def __init__(self, files, input_dir, output_dir, file_table, files_extracted, create_sub_dirs):
        super().__init__()
        self.files = files
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.file_table = file_table
        self.files_extracted = files_extracted
        self.create_sub_dirs = create_sub_dirs

    def run(self):
        for index, filename in enumerate(self.files):
            try:
                extract_textures(self, filename, self.input_dir, self.output_dir, index, self.create_sub_dirs)
                printer("Finished extracting textures from {}\n", filename)
            except Exception as e:
                printer("An error ocurred while trying to extract form {}. The error was: {}\n", filename, e)
                if print_traceback:
                    traceback.print_exc()
                self.progress_signal.emit(index)
        self.extraction_complete_signal.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
