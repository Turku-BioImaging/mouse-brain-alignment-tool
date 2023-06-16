import os

from PyQt5.QtWidgets import QFileDialog, QMainWindow
from PyQt5.uic import loadUi


class SelectDataWindow(QMainWindow):
    data_dir = ""

    def __init__(self):
        super(SelectDataWindow, self).__init__()
        loadUi(
            os.path.join(os.path.dirname(__file__), "..", "gui", "select_data.ui"), self
        )

        self.select_dirpath_push_button.clicked.connect(self.set_data_dir)
        self.continue_push_button.clicked.connect(self.close_window)

    def set_data_dir(self):
        self.data_dir = QFileDialog.getExistingDirectory(self, "Select data directory")
        self.dirpath_line_edit.setText(self.data_dir)
        self.continue_push_button.setEnabled(True)

    def close_window(self):
        self.close()
