import os
import sys
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from traceback import format_exception
from queue import Queue
from multiprocessing import Manager

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
    textures_extracted = 0
    files_processed = 0
    start_time = 0
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
        self.start_time = datetime.now()
        self.progress_bar.setValue(0)
        self.extract_button.setEnabled(False)
        self.worker = Worker(self.current_files, self.current_dir, self.output_dir, self.file_table, self.textures_extracted, self.create_sub_dirs)
        self.worker.progress_signal.connect(self.update_progress_bar)
        self.worker.extraction_complete_signal.connect(self.extraction_complete)
        self.worker.update_file_table_signal.connect(self.update_file_table)
        self.worker.file_extracted_signal.connect(self.increment_textures_extracted)
        self.worker.start()

    @pyqtSlot()
    def update_progress_bar(self):
        self.files_processed += 1
        progress = round(self.files_processed / len(self.current_files) * 100)
        self.progress_bar.setValue(progress)

    @pyqtSlot(int, int, str)
    def update_file_table(self, row, col, text):
        new_item = QTableWidgetItem(text)
        self.file_table.setItem(row, col, new_item)

    @pyqtSlot()
    def increment_textures_extracted(self):
        self.textures_extracted += 1

    @pyqtSlot()
    def extraction_complete(self):
        self.progress_bar.setValue(100)
        self.extract_button.setEnabled(True)
        self.status_bar.showMessage(f"Time elapsed: {(datetime.now() - self.start_time).total_seconds()}")

    def create_sub_dirs_clicked(self):
        self.create_sub_dirs = not self.create_sub_dirs


def process_file(queue, filename, input_dir, output_dir, file_index, create_sub_dirs):
    output_strings = []
    separator = "\n"

    try:
        extract_textures(
            filename,
            input_dir,
            output_dir,
            file_index,
            create_sub_dirs,
            output_strings,
            lambda row, col, text: queue.put(("update_file_table_signal", row, col, text)),
            lambda: queue.put(("file_extracted_signal",)),
            lambda file_index, num_actual_tex, textures_written: queue.put(("update_file_status", file_index, num_actual_tex, textures_written)),
        )
        if printer.on:
            output_strings.append(f"Finished extracting textures from {filename}\n")
    except Exception as e:
        if printer.on:
            output_strings.append(f"An error ocurred while trying to extract form {filename}. The error was: {e}\n")
        if print_traceback:
            traceback.print_exc()
    finally:
        queue.put(("progress_signal",))
        if len(output_strings) > 0:
            print(separator.join(output_strings))


class Worker(QThread):
    progress_signal = pyqtSignal()
    extraction_complete_signal = pyqtSignal()
    update_file_table_signal = pyqtSignal(int, int, str)
    file_extracted_signal = pyqtSignal()

    def __init__(self, files, input_dir, output_dir, file_table, textures_extracted, create_sub_dirs):
        super().__init__()
        self.files = files
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.file_table = file_table
        self.textures_extracted = textures_extracted
        self.create_sub_dirs = create_sub_dirs

    def run(self):
        max_workers = os.cpu_count()

        with Manager() as manager:
            queue = manager.Queue()
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(process_file, queue, filename, self.input_dir, self.output_dir, self.files.index(filename), self.create_sub_dirs) for filename in self.files
                ]

                while True:
                    if all(f.done() for f in futures):
                        break

                    while not queue.empty():
                        signal_type, *args = queue.get()
                        if signal_type == "update_file_table_signal":
                            self.update_file_table_signal.emit(*args)
                        elif signal_type == "file_extracted_signal":
                            self.file_extracted_signal.emit()
                        elif signal_type == "update_file_status":
                            self.update_file_status(*args)
                        elif signal_type == "progress_signal":
                            self.progress_signal.emit()

                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        traceback_msg = "".join(format_exception(exc_type, exc_value, exc_traceback))
                        print(f"An error occurred in the process: {e}\nTraceback: {traceback_msg}")

        self.extraction_complete_signal.emit()

    def update_file_status(self, file_index, num_actual_tex, textures_written):
        if num_actual_tex > 0:
            self.update_file_table_signal.emit(file_index, 2, str(textures_written))
            self.update_file_table_signal.emit(file_index, 3, "OK" if num_actual_tex == textures_written else "ERROR")
        else:
            self.update_file_table_signal.emit(file_index, 2, "0")
            self.update_file_table_signal.emit(file_index, 3, "SKIPPED")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
