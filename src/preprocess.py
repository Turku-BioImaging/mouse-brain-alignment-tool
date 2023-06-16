import os
import subprocess

from PyQt5.QtWidgets import QApplication, QDialog, QFileDialog
from PyQt5.uic import loadUi


class MainWindow(QDialog):
    num_slides = 1
    num_animals = 1
    image_fname = ""
    output_dir = ""
    animal_left_name = ""
    animal_right_name = ""

    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi(os.path.join(os.path.dirname(__file__), "gui", "preprocess.ui"), self)

        self.select_image.clicked.connect(self.set_image_fname)
        self.set_slide_count()
        self.num_slides_1.clicked.connect(self.set_slide_count)
        self.num_slides_2.clicked.connect(self.set_slide_count)

        self.set_animal_count()
        self.num_animals_1.clicked.connect(self.set_animal_count)
        self.num_animals_2.clicked.connect(self.set_animal_count)

        self.animal_left_name_textbox.textChanged.connect(self.set_animal_left_name)
        self.animal_right_name_textbox.textChanged.connect(self.set_animal_right_name)

        self.select_output_directory.clicked.connect(self.set_output_dir)

        self.process.clicked.connect(self.print_output1)
        self.process.clicked.connect(self.run)
        self.process.clicked.connect(self.print_output2)

    def set_slide_count(self):
        if self.num_slides_1.isChecked() is True:
            self.num_slides = 1
        if self.num_slides_2.isChecked() is True:
            self.num_slides = 2

        self.set_animal_count()

    def set_animal_count(self):
        if self.num_animals_1.isChecked() is True:
            self.num_animals = 1
            self.group_animal_names.setEnabled(False)
        if self.num_animals_2.isChecked() is True:
            self.num_animals = 2
            self.group_animal_names.setEnabled(True)

    def set_animal_left_name(self):
        self.animal_left_name = self.animal_left_name_textbox.text()

    def set_animal_right_name(self):
        self.animal_right_name = self.animal_right_name_textbox.text()

    def set_image_fname(self):
        self.image_fname, _ = QFileDialog.getOpenFileName(self, "Select File")
        self.image_fname_textbox.setText(self.image_fname)

    def set_output_dir(self):
        self.output_dir = QFileDialog.getExistingDirectory(self, "Select Directory")
        self.output_directory_textbox.setText(self.output_dir)

    def print_output1(self):
        self.log_textbox.append(f'File: {os.path.basename(self.image_fname)}')
        self.log_textbox.append("Running preprocessing...")
        QApplication.processEvents()

    def print_output2(self):
        self.log_textbox.append("Finished!")
        self.log_textbox.append("")

    def run(self):
        script_path = os.path.join(
            os.path.dirname(__file__), "modules", "preprocessing.py"
        )

        if self.num_animals == 2:
            subprocess.call(
                [
                    "python",
                    script_path,
                    "--image-path",
                    self.image_fname,
                    "--num-slides",
                    str(self.num_slides),
                    "--num-animals",
                    str(self.num_animals),
                    "--animal-left-name",
                    self.animal_left_name,
                    "--animal-right-name",
                    self.animal_right_name,
                    '--output-dir',
                    self.output_dir
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        if self.num_animals == 1:
            subprocess.call(
                [
                    "python",
                    script_path,
                    "--image-path",
                    self.image_fname,
                    "--num-slides",
                    str(self.num_slides),
                    "--num-animals",
                    str(self.num_animals),
                    "--output-dir",
                    self.output_dir,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
