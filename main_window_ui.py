# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\extractorUi.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_main_window(object):
    def setupUi(self, main_window):
        main_window.setObjectName("main_window")
        main_window.resize(640, 480)
        self.main_layout = QtWidgets.QWidget(main_window)
        self.main_layout.setObjectName("main_layout")
        self.gridLayout = QtWidgets.QGridLayout(self.main_layout)
        self.gridLayout.setObjectName("gridLayout")
        self.vertical_layout = QtWidgets.QVBoxLayout()
        self.vertical_layout.setObjectName("vertical_layout")
        self.input_row = QtWidgets.QHBoxLayout()
        self.input_row.setObjectName("input_row")
        self.input_label = QtWidgets.QLabel(self.main_layout)
        self.input_label.setMinimumSize(QtCore.QSize(81, 0))
        self.input_label.setObjectName("input_label")
        self.input_row.addWidget(self.input_label)
        self.input_path = QtWidgets.QLineEdit(self.main_layout)
        self.input_path.setEnabled(True)
        self.input_path.setReadOnly(True)
        self.input_path.setObjectName("input_path")
        self.input_row.addWidget(self.input_path)
        self.input_browse = QtWidgets.QPushButton(self.main_layout)
        self.input_browse.setObjectName("input_browse")
        self.input_row.addWidget(self.input_browse)
        self.vertical_layout.addLayout(self.input_row)
        self.output_row = QtWidgets.QHBoxLayout()
        self.output_row.setObjectName("output_row")
        self.output_label = QtWidgets.QLabel(self.main_layout)
        self.output_label.setMinimumSize(QtCore.QSize(81, 0))
        self.output_label.setObjectName("output_label")
        self.output_row.addWidget(self.output_label)
        self.output_path = QtWidgets.QLineEdit(self.main_layout)
        self.output_path.setReadOnly(True)
        self.output_path.setObjectName("output_path")
        self.output_row.addWidget(self.output_path)
        self.output_browse = QtWidgets.QPushButton(self.main_layout)
        self.output_browse.setObjectName("output_browse")
        self.output_row.addWidget(self.output_browse)
        self.vertical_layout.addLayout(self.output_row)
        self.extract_row = QtWidgets.QHBoxLayout()
        self.extract_row.setObjectName("extract_row")
        self.extract_button = QtWidgets.QPushButton(self.main_layout)
        self.extract_button.setEnabled(False)
        self.extract_button.setCheckable(False)
        self.extract_button.setObjectName("extract_button")
        self.extract_row.addWidget(self.extract_button)
        self.toggle_sub_dirs = QtWidgets.QCheckBox(self.main_layout)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toggle_sub_dirs.sizePolicy().hasHeightForWidth())
        self.toggle_sub_dirs.setSizePolicy(sizePolicy)
        self.toggle_sub_dirs.setToolTipDuration(-1)
        self.toggle_sub_dirs.setObjectName("toggle_sub_dirs")
        self.extract_row.addWidget(self.toggle_sub_dirs)
        self.vertical_layout.addLayout(self.extract_row)
        self.file_table = QtWidgets.QTableWidget(self.main_layout)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setColumnCount(4)
        self.file_table.setObjectName("file_table")
        self.file_table.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.file_table.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.file_table.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.file_table.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.file_table.setHorizontalHeaderItem(3, item)
        self.file_table.horizontalHeader().setVisible(True)
        self.file_table.horizontalHeader().setCascadingSectionResizes(False)
        self.file_table.horizontalHeader().setDefaultSectionSize(120)
        self.vertical_layout.addWidget(self.file_table)
        self.progress_bar = QtWidgets.QProgressBar(self.main_layout)
        self.progress_bar.setProperty("value", 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setObjectName("progress_bar")
        self.vertical_layout.addWidget(self.progress_bar)
        self.gridLayout.addLayout(self.vertical_layout, 0, 0, 1, 1)
        main_window.setCentralWidget(self.main_layout)
        self.status_bar = QtWidgets.QStatusBar(main_window)
        self.status_bar.setObjectName("status_bar")
        main_window.setStatusBar(self.status_bar)
        self.input_label.setBuddy(self.input_path)
        self.output_label.setBuddy(self.output_path)

        self.retranslateUi(main_window)
        self.output_browse.clicked.connect(main_window.output_browse_clicked) # type: ignore
        self.extract_button.clicked.connect(main_window.extract_clicked) # type: ignore
        self.input_browse.clicked.connect(main_window.input_browse_clicked) # type: ignore
        self.toggle_sub_dirs.stateChanged['int'].connect(main_window.create_sub_dirs_clicked) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(main_window)
        main_window.setTabOrder(self.input_path, self.input_browse)
        main_window.setTabOrder(self.input_browse, self.output_path)
        main_window.setTabOrder(self.output_path, self.output_browse)
        main_window.setTabOrder(self.output_browse, self.file_table)

    def retranslateUi(self, main_window):
        _translate = QtCore.QCoreApplication.translate
        main_window.setWindowTitle(_translate("main_window", "PSX Texture Extractor v0.9"))
        self.input_label.setText(_translate("main_window", "Input Directory"))
        self.input_browse.setText(_translate("main_window", "Browse..."))
        self.output_label.setText(_translate("main_window", "Output Directory"))
        self.output_browse.setText(_translate("main_window", "Browse..."))
        self.extract_button.setText(_translate("main_window", "Extract"))
        self.toggle_sub_dirs.setToolTip(_translate("main_window", "When selected, a subdirectory will be created for each PSX file."))
        self.toggle_sub_dirs.setText(_translate("main_window", "Create Subdirectories"))
        self.file_table.setSortingEnabled(True)
        item = self.file_table.horizontalHeaderItem(0)
        item.setText(_translate("main_window", "File Name"))
        item = self.file_table.horizontalHeaderItem(1)
        item.setText(_translate("main_window", "Number of Textures"))
        item = self.file_table.horizontalHeaderItem(2)
        item.setText(_translate("main_window", "Textures Extracted"))
        item = self.file_table.horizontalHeaderItem(3)
        item.setText(_translate("main_window", "Status"))
