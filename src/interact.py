import napari
import os
import sys
import numpy as np
from skimage import io, img_as_ubyte

from skimage.filters import median, threshold_otsu

# from skimage.morphology import remove_small_objects, binary_opening, area_closing
# from skimage.segmentation import watershed
# from skimage.feature import peak_local_max
# from skimage.measure import label, regionprops
# from scipy import ndimage as ndi
# import pandas as pd
from magicgui import magicgui
import pandas as pd

# import ast
import shapely
import argparse
import json
from glob import glob

from modules.classes import Background

ATLAS_DIR = os.path.join(os.path.dirname(__file__), "brain_atlas_files")


global viewer, bg


def _load_atlas_data():
    anatomical_atlas = io.imread(os.path.join(ATLAS_DIR, "anatomical_atlas.tif"))
    rois = io.imread(os.path.join(ATLAS_DIR, "rois_atlas.tif"))

    with open(os.path.join(ATLAS_DIR, "roi_colors.json")) as f:
        data = json.load(f)
        str_roi_list = list(data.keys())
        region_column_names = ["All_rois"] + list(str_roi_list)

    slice_centroids_dict = {}
    df = pd.read_csv(os.path.join(ATLAS_DIR, "slice_centroids.csv"))
    for _, row in df.iterrows():
        slice_centroids_dict[int(row["slice"])] = (row["centroid_y"], row["centroid_x"])

    with open(os.path.join(ATLAS_DIR, "roi_shapes.json")) as f:
        data = json.load(f)
        roi_shapes_dict = data

    return (
        anatomical_atlas,
        rois,
        region_column_names,
        slice_centroids_dict,
        roi_shapes_dict,
    )


def _select_background(args):
    slide_path = glob(os.path.join(args.data_dir, "tiff", "*.tif"))[0]
    bg.image = io.imread(slide_path)
    bg.height, bg.width = int(bg.image.shape[0]), int(bg.image.shape[1])
    rect_y, rect_x = int(bg.height / 2) - 400, int(bg.width / 2) - 200

    viewer.add_image(
        bg.image,
        name="image_scan",
        colormap="gray_r",
        contrast_limits=[0, np.max(bg.image)],
    )
    bg.napari_layer = viewer.add_shapes(opacity=0.4, name="background_area")
    bg_rect = np.array([[rect_y, rect_x], [rect_y + 800, rect_x + 400]])
    bg.napari_layer.add_rectangles(
        bg_rect, edge_width=10, edge_color="red", face_color="orange"
    )

    viewer.window.add_dock_widget(
        [calculate_bg_widget, start_alignment], name="Controls"
    )

    return bg.height, bg.width


def _get_background():
    y = bg.height
    x = bg.width

    canvas_rect = np.array([[0, 0], [y - 1, x - 1]])
    bg.napari_layer.add_rectangles(canvas_rect)  # to keep shape image layer
    bg_labels = bg.napari_layer.to_labels()
    bg.napari_layer.data = bg.napari_layer.data[0 : (len(bg.napari_layer.data) - 1)]
    # mean = slide_img[bg_labels == 1].mean()
    mean = bg.image[bg_labels == 1].mean()
    print(f"Background mean: {mean}")
    return mean


def _initialize_analysis_tool():
    # global roi_layer, image_layer
    # viewer.grid.enabled = True
    # viewer.grid.shape = (1,-1)
    # bg_dock.hide() # removal was giving error
    # atlas_layer = viewer.add_image(
    #     anatomical_stack_rs,
    #     name="anatomical_stack",
    #     contrast_limits=[0, np.max(anatomical_stack_rs)],
    # )
    # roi_layer = viewer.add_image(rois, name="atlas_rois",
    #     colormap = "magma",
    #     contrast_limits=[0, np.max(rois)])
    # image_layer = viewer.add_image(loaded_img, name="image", colormap="gray_r")
    # viewer.window.add_dock_widget([atlas_view, rois_widget, simple_rois_widget, hide_widget, analyze_widget, next_image, previous_image])
    # viewer.reset_view()
    print("test")


@magicgui(call_button="Calculate background")
def calculate_bg_widget():
    # global bg_mean
    bg.mean = 0
    bg.mean = _get_background()


@magicgui(call_button="Start alignment")
def start_alignment():
    viewer.layers.select_all()
    viewer.layers.remove_selected()
    _initialize_analysis_tool()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=str, required=True)
    args = parser.parse_args()

    ## load atlas data
    (
        anatomical_atlas,
        rois,
        region_column_names,
        slice_centroids_dict,
        roi_shapes_dict,
    ) = _load_atlas_data()

    # load images
    image_paths = glob(os.path.join(args.data_dir, "sections", "*.tif"))

    bg = Background()

    # configure napari
    viewer = napari.Viewer()
    _select_background(args)

    napari.run()
