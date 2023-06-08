import argparse
import json
import os
from glob import glob

import napari
import numpy as np
import pandas as pd
import shapely
from magicgui import magicgui
from modules.classes import Atlas, Background, Results, SectionImage
from scipy import ndimage as ndi
from skimage import filters, img_as_ubyte, io, measure, morphology
from skimage.transform import rescale

ATLAS_DIR = os.path.join(os.path.dirname(__file__), "brain_atlas_files")


global viewer, bg, atlas, section_image, section_image_paths, results_data


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

    # scalle down bg image to reduce size
    bg.image = rescale(bg.image, 0.5, anti_aliasing=False, preserve_range=True)
    bg.height, bg.width = int(bg.image.shape[0]), int(bg.image.shape[1])
    rect_y, rect_x = int(bg.height / 2) - 400, int(bg.width / 2) - 200

    viewer.add_image(
        bg.image,
        name="image_scan",
        colormap="gray_r",
        contrast_limits=[0, np.max(bg.image)],
    )
    bg.napari_layer = viewer.add_shapes(opacity=0.4, name="background_area")
    bg_rect = np.array([[rect_y, rect_x], [rect_y + 400, rect_x + 200]])
    bg.napari_layer.add_rectangles(
        bg_rect, edge_width=10, edge_color="red", face_color="orange"
    )

    # Set the mode (tool) of the backgroud shape layer to "select"
    bg.napari_layer.mode = "SELECT"
    # Make active selection of the bacground rectangle
    bg.napari_layer.selected_data = [0]
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
            hide_widget,
            show_all_widget,
            analyze_widget,
            next_image_widget,
            previous_image_widget,
            image_name_widget,
        ]
    )
    image_name_widget.enabled = False

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
    masked_img = _get_image_mask()

    selected_slice = int(viewer.dims.current_step[0])

    center_of_mass_atlas = atlas.slice_centroids_dict[selected_slice]

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
    atlas.selected_slice = selected_slice

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


def _hide_unselected_rois():
    selected = list(atlas.napari_roi_shapes_layer.selected_data)
    selected_names = atlas.napari_roi_shapes_layer.text.string.array[selected]
    color_array = []
    edge_color = []
    iter_t = 0

    for i in range(atlas.napari_roi_shapes_layer.nshapes):
        if i in selected:
            rgb_values = atlas.roi_colors_dict[selected_names[iter_t]][1][:-1]
            opacity_value = atlas.roi_colors_dict[selected_names[iter_t]][1][-1]

            rgb_floats = []

            for i in rgb_values:
                rgb_floats.append(i / 255.0)

            color_array.append(rgb_floats + [opacity_value])
            edge_color.append([1.0, 0.0, 0.0, 1.0])
            iter_t += 1
        else:
            color_array.append([0.0, 0.0, 0.0, 0.0])
            edge_color.append([0.0, 0.0, 0.0, 0.0])

    atlas.napari_roi_shapes_layer.face_color = color_array
    atlas.napari_roi_shapes_layer.edge_color = edge_color  # transparent


def _show_all_rois():
    roi_names = atlas.napari_roi_shapes_layer.text.string.array
    color_array = []
    edge_color = []
    for i in range(atlas.napari_roi_shapes_layer.nshapes):
        rgb_values = atlas.roi_colors_dict[roi_names[i]][1][:-1]
        opacity_value = atlas.roi_colors_dict[roi_names[i]][1][-1]

        rgb_floats = []
        for i in rgb_values:
            rgb_floats.append(i / 255.0)

        color_array.append(rgb_floats + [opacity_value])
        edge_color.append([1.0, 0.0, 0.0, 1.0])
    atlas.napari_roi_shapes_layer.face_color = color_array
    atlas.napari_roi_shapes_layer.edge_color = edge_color


def _get_mapped_labels(label_image: np.ndarray, names: list) -> np.ndarray:
    unique_names = list(set(names))

    mapping_dict = {}
    for name in unique_names:
        matching_indices = [
            index + 1 for index, element in enumerate(names) if element == name
        ]

        mapping_dict[name] = matching_indices

    mapped_label_image = np.copy(label_image)

    for idx, name in enumerate(unique_names):
        label_values = mapping_dict[name]

        for v in label_values:
            mapped_label_image[label_image == v] = idx + 1

    return unique_names, mapped_label_image


def _polygons_to_roi() -> np.ndarray:
    shapes_layer = atlas.napari_roi_shapes_layer

    labels = shapes_layer.to_labels(labels_shape=section_image.image.shape)
    label_names = shapes_layer.text.string.array

    label_names, labels = _get_mapped_labels(labels, label_names)

    return label_names, labels


def _analyze_roi():
    label_names, labels = _polygons_to_roi()
    all_regions = labels > 0

    results_dict = {
        "image_filename": section_image.name,
    }

    # Measure and record values for combined ROIs
    area = np.count_nonzero(all_regions)
    mean = section_image.image[all_regions].mean()

    bg_subtracted_mean_per_pixel = None
    if mean > bg.mean:
        bg_subtracted_mean_per_pixel = (mean - bg.mean) / area
    else:
        bg_subtracted_mean_per_pixel = 0

    results_dict["All_ROIs"] = bg_subtracted_mean_per_pixel

    for region_name in results_data.region_names:
        if region_name == "All_ROIs":
            continue
        if region_name in label_names:
            roi_mean = section_image.image[
                labels == label_names.index(region_name)
            ].mean()

            area = np.count_nonzero(labels == label_names.index(region_name))

            bg_subtracted_mean_per_pixel = (
                roi_mean - bg.mean if roi_mean > bg.mean else 0
            ) / area

            results_dict[region_name] = bg_subtracted_mean_per_pixel
        else:
            results_dict[region_name] = np.nan

    results_data.add_row(results_dict)


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
    _load_selected_rois()


@magicgui(call_button="Hide unselected rois")
def hide_widget():
    _hide_unselected_rois()


@magicgui(call_button="Show all rois")
def show_all_widget():
    _show_all_rois()


@magicgui(call_button="Analyze rois")
def analyze_widget():
    _analyze_roi()


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

        if "atlas_rois" in viewer.layers:
            if viewer.dims.current_step[0] == 0:
                pass
            else:
                section_image.image = _align_centroids()

        if results_data.image_is_analyzed(section_image.name):
            colormap = "green"
        else:
            colormap = "gray_r"

        section_image.napari_layer = viewer.add_image(
            section_image.image, name="section_image", colormap=colormap
        )

        image_name_widget.update(IMG=section_image.name)

        if len(viewer.layers) == 3:
            pass
        else:
            viewer.layers.reverse()
            viewer.layers.selection.active = atlas.napari_roi_shapes_layer
            atlas.napari_roi_shapes_layer.mode = "SELECT"


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

        if "atlas_rois" in viewer.layers:
            if viewer.dims.current_step[0] == 0:
                pass
            else:
                section_image.image = _align_centroids()
        if "atlas_rois" in viewer.layers:
            if viewer.dims.current_step[0] == 0:
                pass
            else:
                section_image.image = _align_centroids()

        if results_data.image_is_analyzed(section_image.name):
            colormap = "green"
        else:
            colormap = "gray_r"

        section_image.napari_layer = viewer.add_image(
            section_image.image, name="section_image", colormap=colormap
        )

        image_name_widget.update(IMG=section_image.name)

        if len(viewer.layers) == 3:
            pass
        else:
            viewer.layers.reverse()
            viewer.layers.selection.active = atlas.napari_roi_shapes_layer
            atlas.napari_roi_shapes_layer.mode = "SELECT"


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

    ## init results data
    results_data = Results(data_dir=args.data_dir)

    # load first section image
    section_image_paths = sorted(glob(os.path.join(args.data_dir, "sections", "*.tif")))
    assert len(section_image_paths) > 0
    section_image = SectionImage(section_image_paths[0])

    @magicgui(call_button=" ")
    def image_name_widget(IMG: str = section_image.name, analyzed: bool = False):
        pass

    bg = Background()

    # configure napari
    viewer = napari.Viewer()
    _select_background(args)

    napari.run()
