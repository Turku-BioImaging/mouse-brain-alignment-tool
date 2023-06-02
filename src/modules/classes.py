import numpy as np
from skimage import io


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
    napari_layer = None

    def __init__(self, path: str):
        self.path = path
        self.image = io.imread(path)
