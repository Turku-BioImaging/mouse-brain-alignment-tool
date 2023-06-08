import json
import os

import numpy as np
import pandas as pd
from skimage import io

ATLAS_DIR = os.path.join(os.path.dirname(__file__), "..", "brain_atlas_files")


class Background:
    height = None
    width = None
    mean = None
    image = None
    napari_layer = None
    napari_dock = None

    def __init__(self):
        self.height = 0
        self.width = 0
        self.mean = 0
        self.image = None
        self.napari_layer = None
        self.napari_dock = None


class Atlas:
    image = None
    rois = None
    region_column_names = None
    slice_centroids_dict = None
    roi_shapes_dict = None
    selected_slice = None

    napari_atlas_layer = None
    napari_roi_shapes_layer = None
    napari_roi_layer = None

    def __init__(
        self,
        image: np.ndarray = None,
        rois: np.ndarray = None,
        region_column_names: list = None,
        slice_centroids_dict: dict = None,
        roi_shapes_dict: dict = None,
        roi_colors_dict: dict = None,
    ):
        self.image = image
        self.rois = rois
        self.region_column_names = region_column_names
        self.slice_centroids_dict = slice_centroids_dict
        self.roi_shapes_dict = roi_shapes_dict
        self.roi_colors_dict = roi_colors_dict


class SectionImage:
    path = None
    image = None
    name = None
    napari_layer = None

    def __init__(self, path: str):
        self.path = path
        self.image = io.imread(path)
        self.name = os.path.basename(path)


class Results:
    region_names = None
    data = None
    data_path = None

    def __init__(self, data_dir: str = None):
        # init dataframe or load from csv
        with open(os.path.join(ATLAS_DIR, "roi_colors.json")) as f:
            data = json.load(f)
            self.region_names = ["All_ROIs"] + list(data.keys())

        assert os.path.isdir(data_dir)
        self.data_path = os.path.join(data_dir, "results.csv")
        self._init_data()

    def _init_data(self):
        # check if csv exists
        # check that column headers are correct
        # load into dataframe
        if os.path.isfile(self.data_path):
            read_data = pd.read_csv(self.data_path)
            expected_columns = ["image_filename"] + self.region_names
            if read_data.columns.to_list() == expected_columns:
                self.data = read_data
            else:
                self.data = pd.DataFrame(columns=["image_filename"] + self.region_names)

        # else init a new empty dataframe and save to csv
        else:
            self.data = pd.DataFrame(columns=["image_filename"] + self.region_names)
            self.data.to_csv(self.data_path, index=False)

    def add_row(self, row: dict):
        assert all(key in row for key in self.region_names + ["image_filename"])

        if row["image_filename"] in self.data["image_filename"].values:
            self.data.loc[
                self.data["image_filename"] == row["image_filename"]
            ] = row.values()

        else:
            new_row = pd.DataFrame([row])
            self.data = pd.concat([self.data, new_row], ignore_index=True)
            self.data = self.data.sort_values("image_filename")

        self.data.to_csv(self.data_path, index=False)

    def image_is_analyzed(self, image_filename: str) -> bool:
        
        if image_filename in self.data['image_filename'].values:
            return True
        
        return False
