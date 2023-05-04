import os
import sys
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from multiprocessing import Manager
from traceback import format_exception

from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QTableWidgetItem

from io_thps_scene import extract_textures
from main_window_ui import Ui_main_window

print_output = True
print_traceback = True


# Define main window class, inherits QMainWindow and Ui_main_window
class Window(QMainWindow, Ui_main_window):
    current_dir = ""
    output_dir = ""
    current_files = []
    files_processed = 0
    start_time = 0
    create_sub_dirs = False

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

    # Open a directory picker and set the input directory path
    def input_browse_clicked(self):
        options = QFileDialog.Options()
        dir_name = QFileDialog.getExistingDirectory(self, "Choose Directory", "", options=options)
        if dir_name:
            self.current_dir = dir_name
            self.current_files = []
            self.file_table.setRowCount(0)
            self.get_psx_files(dir_name)

    # Filter files with .psx or .PSX extensions
    def filter_psx_files(self, file_list):
        return [f for f in file_list if f.lower().endswith((".psx", ".PSX"))]

    # Get .psx files from the chosen directory and update the GUI
    def get_psx_files(self, dir_name):
        self.input_path.setText(dir_name)
        dir_files = [f for f in os.listdir(dir_name) if os.path.isfile(os.path.join(dir_name, f))]
        psx_files = list(self.filter_psx_files(dir_files))
        if len(psx_files) > 0:
            self.file_table.setRowCount(len(psx_files))
            for row, file in enumerate(psx_files):
                self.current_files.append(file)
                self.file_table.setItem(row, 0, QTableWidgetItem(file))
            if self.output_dir:
                self.extract_button.setEnabled(True)
        else:
            self.extract_button.setEnabled(False)

    # Open a directory picker and set the output directory path
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

    # Start the extraction process when the extract button is clicked
    def extract_clicked(self):
        self.start_time = datetime.now()
        self.progress_bar.setValue(0)
        self.extract_button.setEnabled(False)
        self.worker = Worker(self.current_files, self.current_dir, self.output_dir, self.file_table, self.create_sub_dirs)
        self.worker.update_progress_bar_signal.connect(self.update_progress_bar)
        self.worker.extraction_complete_signal.connect(self.extraction_complete)
        self.worker.update_file_table_signal.connect(self.update_file_table)
        self.worker.start()

    # Update the progress bar based on the number of files processed
    @pyqtSlot()
    def update_progress_bar(self):
        self.files_processed += 1
        progress = round(self.files_processed / len(self.current_files) * 100)
        self.progress_bar.setValue(progress)

    # Update the file table in the GUI
    @pyqtSlot(int, int, str)
    def update_file_table(self, row, col, text):
        new_item = QTableWidgetItem(text)
        self.file_table.setItem(row, col, new_item)

    # Update the UI and display the time elapsed when the extraction is complete
    @pyqtSlot()
    def extraction_complete(self):
        self.progress_bar.setValue(100)
        self.extract_button.setEnabled(True)
        self.status_bar.showMessage(f"Time elapsed: {(datetime.now() - self.start_time).total_seconds()}")

    # Toggle the create_sub_dirs boolean when the Create Subdirectories checkbox is clicked
    def create_sub_dirs_clicked(self):
        self.create_sub_dirs = not self.create_sub_dirs


# Function to process a single file
def process_file(queue, filename, input_dir, output_dir, file_index, create_sub_dirs):
    output_strings = []
    separator = "\n"

    def update_file_table(row, cols):
        for col, text in cols.items():
            queue.put(("update_file_table_signal", row, col, text))

    try:
        extract_textures(filename, input_dir, output_dir, file_index, create_sub_dirs, output_strings, update_file_table)
        if print_output:
            output_strings.append(f"Finished extracting textures from {filename}\n")
    except Exception as e:
        if print_output:
            output_strings.append(f"An error occurred while trying to extract from {filename}. The error was: {e}\n")
        if print_traceback:
            traceback.print_exc()
    finally:
        queue.put(("update_progress_bar_signal",))
        if print_output and len(output_strings) > 0:
            print(separator.join(output_strings))


# Define the worker thread class, inherits QThread
class Worker(QThread):
    # Define custom PyQt signals for progress, completion, and updating the file table
    update_progress_bar_signal = pyqtSignal()
    update_file_table_signal = pyqtSignal(int, int, str)
    extraction_complete_signal = pyqtSignal()

    def __init__(self, files, input_dir, output_dir, file_table, create_sub_dirs):
        super().__init__()
        # Initialize instance variables
        self.files = files
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.file_table = file_table
        self.create_sub_dirs = create_sub_dirs

    # Run the worker thread
    def run(self):
        # Get the number of available CPU cores
        max_workers = os.cpu_count()

        # Use a Manager for inter-process communication
        with Manager() as manager:
            queue = manager.Queue()  # Create a queue for sharing data between processes
            # Use a ProcessPoolExecutor for parallel processing
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                # Submit each file for processing and store the resulting Future objects
                futures = [
                    executor.submit(process_file, queue, filename, self.input_dir, self.output_dir, self.files.index(filename), self.create_sub_dirs) for filename in self.files
                ]

                # Continuously check if all futures are done
                while True:
                    if all(f.done() for f in futures):
                        break

                    # Process items in the queue until it is empty
                    while not queue.empty():
                        signal_type, *args = queue.get()
                        if signal_type == "update_file_table_signal":
                            self.update_file_table_signal.emit(*args)
                        elif signal_type == "progress_signal":
                            self.progress_signal.emit()

                # Iterate through the completed futures and handle any exceptions
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        traceback_msg = "".join(format_exception(exc_type, exc_value, exc_traceback))
                        print(f"An error occurred in the process: {e}\nTraceback: {traceback_msg}")

        # Emit the extraction complete signal to inform the GUI that the process is done
        self.extraction_complete_signal.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
