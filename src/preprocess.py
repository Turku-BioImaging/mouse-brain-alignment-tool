import os
import pandas as pd
from PyQt5.QtWidgets import QApplication, QDialog, QFileDialog
from PyQt5.uic import loadUi
import modules.preprocessing as preprocessing
from modules import constants
import pyi_splash


def _load_excel_data(data_dir: str):
    assert os.path.isdir(data_dir), "Data directory does not exist"
    assert os.path.isfile(
        os.path.join(data_dir, "data.xlsx")
    ), "data.xlsx does not exist"

    df = pd.read_excel(os.path.join(data_dir, "data.xlsx"))

    return df


def _get_slide_dict(data: pd.DataFrame, input_dir: str):
    data_dict = {
        "image_path": os.path.join(input_dir, data["image_filename"]),
        "num_slides": data["num_slides"],
        "num_animals": data["num_animals"],
        "animal_left_name": data["animal_left_name"],
        "animal_right_name": data["animal_right_name"],
    }

    if data_dict["num_animals"] == 2:
        left = data_dict["animal_left_name"]
        right = data_dict["animal_right_name"]

        assert (
            type(left) == str and len(left) > 0
        ), f"{data_dict['image_path']} is missing animal_left_name"

        assert (
            type(right) == str and len(right) > 0
        ), f"{data_dict['image_path']} is missing animal_right_name"

    return data_dict


class MainWindow(QDialog):
    input_dir = None
    output_dir = None
    data = None

    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi(os.path.join(os.path.dirname(__file__), "gui", "preprocess.ui"), self)

        self.select_source_dir_button.clicked.connect(self.set_input_dir)
        self.select_output_directory.clicked.connect(self.set_output_dir)

        self.run_button.clicked.connect(self.run)
        self.version_label.setText(f"Version: {constants.DIST_VERSION}")

    def set_input_dir(self):
        self.input_dir = os.path.normpath(
            QFileDialog.getExistingDirectory(self, "Select Directory")
        )
        self.source_dir_textbox.setText(self.input_dir)
        self.data = _load_excel_data(self.input_dir)

    def set_output_dir(self):
        self.output_dir = os.path.normpath(
            QFileDialog.getExistingDirectory(self, "Select Directory")
        )
        self.output_dir_textbox.setText(self.output_dir)

    def log_processing_output(self, index_str: str, image_fname: str):
        self.log_textbox.append(
            f"({index_str}) Preprocessing {os.path.basename(image_fname)}..."
        )
        QApplication.processEvents()

    def log_finished_output(self):
        self.log_textbox.append("")
        self.log_textbox.append("PREPROCESSING COMPLETE.")
        self.log_textbox.append("")

    def run(self):
        self.run_button.setEnabled(False)
        self.select_source_dir_button.setEnabled(False)
        self.select_output_directory.setEnabled(False)
        assert self.data is not None, "Data not loaded."
        assert type(self.data) == pd.DataFrame, "Data is not a pandas DataFrame."

        # script_path = os.path.join(
        #     os.path.dirname(__file__), "modules", "preprocessing.py"
        # )
        num_files = len(self.data)

        # loop through dataframe and run processing
        for index, row in self.data.iterrows():
            data = _get_slide_dict(data=row, input_dir=self.input_dir)

            self.log_processing_output(f"{index + 1} / {num_files}", data["image_path"])

            if data["num_animals"] == 2:
                preprocessing.run(
                    image_path=data["image_path"],
                    num_slides=data["num_slides"],
                    num_animals=data["num_animals"],
                    animal_left_name=data["animal_left_name"],
                    animal_right_name=data["animal_right_name"],
                    output_dir=self.output_dir,
                )

            if data["num_animals"] == 1:
                preprocessing.run(
                    image_path=data["image_path"],
                    num_slides=data["num_slides"],
                    num_animals=data["num_animals"],
                    output_dir=self.output_dir,
                )

        self.log_finished_output()
        self.run_button.setEnabled(True)
        self.select_source_dir_button.setEnabled(True)
        self.select_output_directory.setEnabled(True)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    pyi_splash.close()
    app.exec_()
    