# import ast
import shapely
import argparse
import json
import os
from glob import glob

import napari

# import sys
import numpy as np
import pandas as pd

# import pandas as pd
from magicgui import magicgui
from modules.classes import Atlas, Background, SectionImage

# from skimage.morphology import remove_small_objects, binary_opening, area_closing
# from skimage.segmentation import watershed
# from skimage.feature import peak_local_max
# from skimage.measure import label, regionprops
from scipy import ndimage as ndi

# from skimage.filters import median, threshold_otsu
from skimage import filters, img_as_ubyte, io, morphology, measure

ATLAS_DIR = os.path.join(os.path.dirname(__file__), "brain_atlas_files")


global viewer, bg, atlas, section_image, section_image_paths


def _load_section_image(path: int):
    global section_image
    section_image = SectionImage(path)


def _load_atlas_data():
    anatomical_atlas = io.imread(os.path.join(ATLAS_DIR, "anatomical_atlas.tif"))
    rois = io.imread(os.path.join(ATLAS_DIR, "rois_atlas.tif"))

    with open(os.path.join(ATLAS_DIR, "roi_colors.json")) as f:
        data = json.load(f)
        str_roi_list = list(data.keys())
        region_column_names = ["All_rois"] + list(str_roi_list)
        roi_colors_dict = data

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
        roi_colors_dict,
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
        section_image.image, name="section_image", colormap="gray_r"
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


def _get_image_mask():
    blurred = filters.median(section_image.image, np.ones((11, 11)))
    threshold_value = filters.threshold_otsu(blurred)
    thresholded = blurred > threshold_value
    fill_holes = ndi.binary_fill_holes(thresholded)
    fill_holes = ndi.binary_opening(fill_holes, np.ones((5, 5)))

    large_objects_only = img_as_ubyte(
        morphology.remove_small_objects(fill_holes, min_size=6000)
    )

    mask_img = measure.label(large_objects_only)
    return mask_img


def _align_centroids():
    # print('test')
    # return
    masked_img = _get_image_mask()

    selected_slice = int(viewer.dims.current_step[0])

    center_of_mass_atlas = atlas.slice_centroids_dict[selected_slice]
    # print(viewer.dims)

    props_img = measure.regionprops(measure.label(masked_img))
    center_of_mass_image = props_img[0].centroid

    image = np.roll(
        section_image.image,
        -int(center_of_mass_image[1] - center_of_mass_atlas[1]),
        axis=1,
    )

    image = np.roll(
        section_image.image,
        -int(center_of_mass_image[0] - center_of_mass_atlas[0]),
        axis=0,
    )

    return image


def _load_selected_rois(simplification: int = 0):
    selected_slice = int(viewer.dims.current_step[0])
    viewer.grid.enabled = False
    viewer.layers.select_all()
    viewer.layers.remove_selected()

    section_image.napari_layer = viewer.add_image(
        section_image.image, name="section_image", colormap="gray_r"
    )

    roi_names = []
    atlas.napari_roi_shapes_layer = viewer.add_shapes(opacity=0.4, name="rois")

    shapes_layer = atlas.napari_roi_shapes_layer
    colors_dict = atlas.roi_colors_dict

    for roi in atlas.roi_shapes_dict[str(selected_slice)]:
        polygon_list_coords = atlas.roi_shapes_dict[str(selected_slice)][roi]
        polygon_simplified = _simplify_polygons(polygon_list_coords, simplification)

        if len(polygon_list_coords) > 0:
            roi_names.extend([roi] * len(polygon_list_coords))

            rgb_values = colors_dict[roi][1][:-1]
            opacity_value = colors_dict[roi][1][-1]


            rgb_floats = []
            for i in rgb_values:
                rgb_floats.append(i / 255.0)

            shapes_layer.add_polygons(
                np.array(polygon_simplified, dtype=object),
                edge_width=2,
                edge_color="red",
                face_color=rgb_floats + [opacity_value],
            )

    shapes_layer.text = {
        "string": roi_names,
        "anchor": "center",
        "translation": [0, 0],
        "size": 15,
        "color": "black",
    }


def _simplify_polygons(input_polygon, tolerance_value):
    contours_s = []
    for shape in input_polygon:
        poly = shapely.geometry.Polygon(shape)
        poly_s = poly.simplify(tolerance=tolerance_value)
        contours_s.append(np.array(poly_s.boundary.coords[:]))
    return contours_s


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
    # print("Add ROIs / Reset")
    _load_selected_rois()


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
        section_image.image, name="section_image", colormap="gray_r"
    )
    viewer.reset_view()


@magicgui(call_button="Next image")
def next_image_widget():
    global section_image
    section_image_paths_index = section_image_paths.index(section_image.path)

    if section_image_paths_index == len(section_image_paths) - 1:
        pass
    else:
        if "section_image" in viewer.layers:
            viewer.layers.remove("section_image")
        section_image_paths_index += 1
        section_image = SectionImage(section_image_paths[section_image_paths_index])

        section_image.image = _align_centroids()
        section_image.napari_layer = viewer.add_image(
            section_image.image, name="section_image", colormap="gray_r"
        )
        if len(viewer.layers) == 3:
            pass
        else:
            viewer.layers.reverse()


@magicgui(call_button="Previous image")
def previous_image_widget():
    global section_image
    section_image_paths_index = section_image_paths.index(section_image.path)

    if section_image_paths_index == 0:
        pass
    else:
        if "section_image" in viewer.layers:
            viewer.layers.remove("section_image")
        section_image_paths_index -= 1
        section_image = SectionImage(section_image_paths[section_image_paths_index])
        section_image.image = _align_centroids()
        section_image.napari_layer = viewer.add_image(
            section_image.image, name="section_image", colormap="gray_r"
        )

        if len(viewer.layers) == 3:
            pass
        else:
            viewer.layers.reverse()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=str, required=True)
    args = parser.parse_args()

    ## load and configure atlas data
    (
        anatomical_atlas,
        rois,
        region_column_names,
        slice_centroids_dict,
        roi_shapes_dict,
        roi_colors_dict,
    ) = _load_atlas_data()

    atlas = Atlas(
        image=anatomical_atlas,
        rois=rois,
        region_column_names=region_column_names,
        slice_centroids_dict=slice_centroids_dict,
        roi_shapes_dict=roi_shapes_dict,
        roi_colors_dict=roi_colors_dict,
    )

    # load first section image
    section_image_paths = sorted(glob(os.path.join(args.data_dir, "sections", "*.tif")))
    assert len(section_image_paths) > 0
    _load_section_image(section_image_paths[0])

    bg = Background()

    # configure napari
    viewer = napari.Viewer()
    _select_background(args)

    napari.run()
