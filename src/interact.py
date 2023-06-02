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

from modules.classes import Background, Atlas, SectionImage

ATLAS_DIR = os.path.join(os.path.dirname(__file__), "brain_atlas_files")


global viewer, bg, atlas, section_image


def _load_section_image(data_dir: str, number: int):
    global section_image
    image_paths = sorted(glob(os.path.join(data_dir, "sections", "*.tif")))
    selected_path = image_paths[number]
    section_image = SectionImage(selected_path)


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

    bg.napari_dock = viewer.window.add_dock_widget(
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
    viewer.grid.enabled = True
    viewer.grid.shape = (1, -1)
    bg.napari_dock.hide()

    atlas.napari_atlas_layer = viewer.add_image(
        atlas.image, name="anatomical_stack", contrast_limits=[0, np.max(atlas.image)]
    )

    atlas.napari_roi_layer = viewer.add_image(
        atlas.rois,
        name="atlas_rois",
        colormap="turbo",
        contrast_limits=[0, np.max(atlas.rois)],
    )

    section_image.napari_layer = viewer.add_image(
        section_image.image, name="image", colormap="gray_r"
    )

    viewer.window.add_dock_widget(
        [
            atlas_view_widget,
            rois_widget,
            simple_rois_widget,
            hide_widget,
            analyze_widget,
            next_image_widget,
            previous_image_widget,
        ]
    )

    viewer.reset_view()


@magicgui(call_button="Calculate background")
def calculate_bg_widget():
    bg.mean = 0
    bg.mean = _get_background()


@magicgui(call_button="Start alignment")
def start_alignment():
    viewer.layers.select_all()
    viewer.layers.remove_selected()
    _initialize_analysis_tool()


@magicgui(call_button="Add ROIs / Reset")
def rois_widget():
    # _load_selected_rois(bg.image)
    print("Add ROIs / Reset")


@magicgui(call_button="Simplify ROIs")
def simple_rois_widget():
    # load_selected_rois(loaded_img, 4)
    print("Simplify rois")


@magicgui(call_button="Hide unselected rois")
def hide_widget():
    # shape_transparency()
    print("Hide unselected rois")


@magicgui(call_button="Analyze rois")
def analyze_widget():
    # roi_analyzer()
    print("Analyze rois")


@magicgui(call_button="Brain Atlas")
def atlas_view_widget():
    viewer.grid.enabled = True
    viewer.grid.shape = (1, -1)
    viewer.layers.select_all()
    viewer.layers.remove_selected()
    atlas.napari_atlas_layer = viewer.add_image(
        atlas.image, name="anatomical_stack", contrast_limits=[0, np.max(atlas.image)]
    )

    atlas.napari_roi_layer = viewer.add_image(
        atlas.rois,
        name="atlas_rois",
        colormap="turbo",
        contrast_limits=[0, np.max(atlas.rois)],
    )

    section_image.napari_layer = viewer.add_image(
        section_image.image, name="image", colormap="gray_r"
    )
    viewer.reset_view()


@magicgui(call_button="Next image")
def next_image_widget():
    # global loaded_img
    # selected_slice = int(roi_layer.position[0]) # get atlas slice position
    # actual = list_names.index(imgname)
    # if actual == len(list_names):
    #     pass
    # else:
    #     image_loader(actual+1)
    #     viewer.layers.remove("image")
    #     loaded_img = align_centroids(loaded_img)
    #     image_layer = viewer.add_image(loaded_img, name="image", colormap="gray_r")
    #     if len(viewer.layers) == 3: # when brain atlas view is on
    #         pass
    #     else:
    #         viewer.layers.reverse()
    #     print(imgname)
    # #viewer.layers.select_previous()
    # #viewer.layers[0].mode = "SELECT"
    print("Next image")


@magicgui(call_button="Previous image")
def previous_image_widget():
    # global loaded_img
    # selected_slice = int(roi_layer.position[0]) # get atlas slice position
    # actual = list_names.index(imgname)
    # if actual == 0:
    #     pass
    # else:
    #     image_loader(actual-1)
    #     viewer.layers.remove("image")
    #     loaded_img = align_centroids(loaded_img)
    #     image_layer = viewer.add_image(loaded_img, name="image", colormap="gray_r")
    #     if len(viewer.layers) == 3: # when brain atlas view is on
    #         pass
    #     else:
    #         viewer.layers.reverse()
    #     print(imgname)
    # #viewer.layers.select_previous()
    # #viewer.layers[0].mode = "SELECT"
    print("Previous image")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=str, required=True)
    parser.add_argument("--image-number", type=int, required=True)
    args = parser.parse_args()

    ## load and configure atlas data
    (
        anatomical_atlas,
        rois,
        region_column_names,
        slice_centroids_dict,
        roi_shapes_dict,
    ) = _load_atlas_data()

    atlas = Atlas(
        image=anatomical_atlas, rois=rois, region_column_names=region_column_names
    )

    # load selected section image
    _load_section_image(args.data_dir, args.image_number)

    bg = Background()

    # configure napari
    viewer = napari.Viewer()
    _select_background(args)

    napari.run()
