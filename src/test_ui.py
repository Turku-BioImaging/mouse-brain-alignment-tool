<<<<<<< HEAD
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QAction,
)
import sys

window_titles = [
    "My App",
    "My App",
    "Still My App",
    "Still My App",
    "What on earth",
    "What on earth",
    "This is surprising",
    "This is surprising",
    "Something went wrong",
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.show()

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)

    def on_context_menu(self, pos):
        context = QMenu(self)
        context.addAction(QAction("test 1", self))
        context.addAction(QAction("test 2", self))
        context.addAction(QAction("test 3", self))
        context.exec(self.mapToGlobal(pos))

    def mousePressEvent(self, e):
        print("Mouse pressed!")
        super().contextMenuEvent(e)


app = QApplication(sys.argv)


window = MainWindow()
# window.show()
app.exec()
=======
import sys
import os
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog
from PyQt5.uic import loadUi
import subprocess


class MainWindow(QDialog):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi(os.path.join("qt_gui", "preprocess.ui"), self)
        self.browse.clicked.connect(self.browse_folder)
        self.row_count()
        self.animal_count()
        self.rows_1.clicked.connect(self.row_count)
        self.rows_2.clicked.connect(self.row_count)
        self.animals_1.clicked.connect(self.animal_count)
        self.animals_2.clicked.connect(self.animal_count)
        self.process.clicked.connect(self.run)

    def row_count(self):
        global n_rows
        n_rows = "2"
        self.group_animals.setEnabled(True)
        self.animal_names.setEnabled(True)
        if self.rows_1.isChecked() is True:
            n_rows = "1"
            self.group_animals.setEnabled(False)
            self.animal_names.setEnabled(False)

    def animal_count(self):
        global n_animals
        n_animals = 2
        self.animal_names.setEnabled(True)
        if self.animals_1.isChecked() is True:
            n_animals = 1
            self.animal_names.setEnabled(False)

    def browse_folder(self):
        global fname
        fname = os.path.join(
            QFileDialog.getExistingDirectory(
                self,
                "Select Directory",
                os.path.join(os.getcwd(), "data"),
            ),
            "",
        )

        self.foldername.setText(fname)

    def run(self):
        name_bottom, name_top = self.animal_left.text(), self.animal_right.text()
        
        if self.animal_names.isEnabled() is True:
            n_animals = "2"
            subprocess.call(
                f"python preprocess_slides.py {fname} {n_rows} {n_animals} {name_top} {name_bottom}",
                shell=True,
            )
        else:
            n_animals = "1"
            subprocess.call(
                f"python preprocess_slides.py {fname} {n_rows} {n_animals}", shell=True
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
>>>>>>> refactor-ui
