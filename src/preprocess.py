import os
import subprocess
import pandas as pd
from glob import glob
from PyQt5.QtWidgets import QApplication, QDialog, QFileDialog
from PyQt5.uic import loadUi


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

        # self.run_button.clicked.connect(self.print_output1)
        self.run_button.clicked.connect(self.run)
        # self.run_button.clicked.connect(self.print_output2)

    def set_input_dir(self):
        self.input_dir = QFileDialog.getExistingDirectory(self, "Select Directory")
        self.source_dir_textbox.setText(self.input_dir)
        self.data = _load_excel_data(self.input_dir)

    def set_output_dir(self):
        self.output_dir = QFileDialog.getExistingDirectory(self, "Select Directory")
        self.output_dir_textbox.setText(self.output_dir)

    # def print_output1(self):
    #     self.log_textbox.append(f"File: {os.path.basename(self.image_fname)}")
    #     self.log_textbox.append("Running preprocessing...")
    #     QApplication.processEvents()

    def print_output2(self):
        self.log_textbox.append("Finished!")
        self.log_textbox.append("")

    def run(self):
        assert self.data is not None, "Data not loaded."
        assert type(self.data) == pd.DataFrame, "Data is not a pandas DataFrame."

        # loop through dataframe and run processing
        for _, row in self.data.iterrows():
            data_dict = _get_slide_dict(data=row, input_dir=self.input_dir)
            print(data_dict)

        # script_path = os.path.join(
        #     os.path.dirname(__file__), "modules", "preprocessing.py"
        # )

        # if self.num_animals == 2:
        #     subprocess.call(
        #         [
        #             "python",
        #             script_path,
        #             "--image-path",
        #             self.image_fname,
        #             "--num-slides",
        #             str(self.num_slides),
        #             "--num-animals",
        #             str(self.num_animals),
        #             "--animal-left-name",
        #             self.animal_left_name,
        #             "--animal-right-name",
        #             self.animal_right_name,
        #             '--output-dir',
        #             self.output_dir
        #         ],
        #         stdout=subprocess.PIPE,
        #         stderr=subprocess.PIPE,
        #     )

        # if self.num_animals == 1:
        #     subprocess.call(
        #         [
        #             "python",
        #             script_path,
        #             "--image-path",
        #             self.image_fname,
        #             "--num-slides",
        #             str(self.num_slides),
        #             "--num-animals",
        #             str(self.num_animals),
        #             "--output-dir",
        #             self.output_dir,
        #         ],
        #         stdout=subprocess.PIPE,
        #         stderr=subprocess.PIPE,
        #     )


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
