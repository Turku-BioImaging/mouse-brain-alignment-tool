"""
MODULE: Brain atlas setup

This module extracts the brain atlas from the brain atlas API and saves it as a TIFF. 
ROIs from selected brain regions are saved in a TIFF stack using randomly selected
colors, and then converted to multipolygons and saved to a JSON dictionary. 
The atlas and related files are stored in the brain_atlas_files folder.

Original code from Zuzana Čočková, modified by Junel Solis.
Turku PET Centre, University of Turku, Finland
Turku BioImaging, University of Turku and Åbo Akademi University, Finland
"""

import os
import numpy as np
import shutil
import shapely
import random
import napari
import argparse
import json
import pandas as pd
import multiprocessing as mp

from bg_atlasapi import BrainGlobeAtlas as bga
from skimage.morphology import remove_small_objects
from skimage.measure import label, regionprops
from skimage.transform import rescale
from skimage import io
from rasterio import features, Affine
from scipy import ndimage as ndi
from tqdm import tqdm


TEMP_PATH = "temp"
ATLAS_PATH = "brain_atlas_files"
SELECTED_ATLAS = "allen_mouse_100um"
SELECTED_REGIONS = (
    "CB",
    "MY",
    "P",
    "MB",
    "HY",
    "TH",
    "PAL",
    "STR",
    "OLF",
    "Isocortex",
    "HIP",
    "RHP",
    "CTXsp",
)
PAD_WIDTHS = ((0, 0), (140, 140), (72, 72))

viewer = None


def mask_to_polygons(mask):
    all_polygons = []

    for shape, _ in features.shapes(
        mask.astype(np.int16),
        mask=(mask > 0),
        transform=Affine(1.0, 0, 0, 0, 1.0, 0),
    ):
        all_polygons.append(shapely.geometry.shape(shape))

    all_polygons = shapely.geometry.MultiPolygon(all_polygons)

    if not all_polygons.is_valid:
        all_polygons = all_polygons.buffer(0)

    if all_polygons.geom_type == "Polygon":
        all_polygons = shapely.geometry.MultiPolygon([all_polygons])

    return all_polygons


def _assign_region_colors():
    list_colors = []
    n = len(SELECTED_REGIONS)

    for _ in range(n):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        rgba = [r, g, b, 0.2]
        list_colors.append(rgba)

    roi_colors_dict = {
        SELECTED_REGIONS[a]: [a + 1, list_colors[a]]
        for a, _ in enumerate(SELECTED_REGIONS)
    }

    with open(os.path.join(ATLAS_PATH, "roi_colors_dict.txt"), "w") as f:
        f.write(str(roi_colors_dict))

    with open(os.path.join(ATLAS_PATH, "roi_colors.json"), "w") as f:
        json.dump(roi_colors_dict, f)


def shapely_shaper(region, slice):
    roi_t = bga(SELECTED_ATLAS).get_structure_mask(region)

    slice_t = roi_t[slice]

    slice_t = slice_t > 0
    slice_t = ndi.binary_fill_holes(slice_t).astype(slice_t.dtype)
    slice_t = remove_small_objects(slice_t)
    slice_t = ndi.binary_erosion(slice_t).astype(slice_t.dtype)
    slice_t = np.pad(
        (rescale(slice_t, (4, 4), anti_aliasing=False, order=0)),
        pad_width=((140, 140), (72, 72)),
    )

    if region == "Isocortex":
        # split isocortex shape in half
        slice_t[:, 300] = 0

    polygon = mask_to_polygons(slice_t)

    return polygon


def _convert_slice_region_to_multipolygons(slice: int, region: str):
    region_polygon = shapely_shaper(region, slice)

    polygons_list = []

    if len(region_polygon.geoms) > 0:
        for polygon in region_polygon.geoms:
            polygons_list.append(
                (
                    np.flip(
                        np.array(polygon.exterior.coords).astype(np.int16),
                        axis=1,
                    )
                ).tolist()
            )

    return {"region": region, "polygons_list": polygons_list}


def _prepare_atlas():
    bg_atlas = bga(SELECTED_ATLAS)

    # anatomical atlas
    anatomical_stack = bg_atlas.reference
    n_slices = anatomical_stack.shape[0]

    anatomical_stack_rs = np.pad(
        (rescale(anatomical_stack, (1, 4, 4), anti_aliasing=True)),
        pad_width=((0, 0), (140, 140), (72, 72)),
    )

    # to match 600,600 xy-shape and pixel size of images, values might be
    # different for other atlases
    io.imsave(
        os.path.join(ATLAS_PATH, "anatomical_atlas.tif"),
        anatomical_stack_rs,
        check_contrast=False,
    )

    # atlas slices centroids
    brain_mask = bg_atlas.get_structure_mask(8)  # dtype np.uint32

    # brain_mask = brain_mask / brain_mask.max()
    brain_mask = np.pad(
        (rescale(brain_mask, (1, 4, 4), anti_aliasing=True, order=0)),
        pad_width=PAD_WIDTHS,
    )

    filled_brain_mask = ndi.binary_dilation(brain_mask)

    for i in range(n_slices):
        filled_brain_mask[i] = ndi.binary_fill_holes(filled_brain_mask[i])

    filled_brain_mask = ndi.binary_erosion(filled_brain_mask)

    slice_centroids = []
    for i in range(n_slices):
        props_atlas = regionprops(label(filled_brain_mask[i]))
        if len(props_atlas) > 0:
            center_of_mass = props_atlas[0].centroid

            slice_centroids.append(
                {
                    "slice": i,
                    "centroid_y": center_of_mass[0],
                    "centroid_x": center_of_mass[1],
                }
            )

    df = pd.DataFrame(slice_centroids)
    df.to_csv(os.path.join(ATLAS_PATH, "slice_centroids.csv"), index=False)

    # get regions of interest
    rois = np.empty((n_slices, 600, 600))
    for reg in SELECTED_REGIONS:
        mask_t = bg_atlas.get_structure_mask(reg)
        mask_t = np.pad(
            (rescale(mask_t, (1, 4, 4), anti_aliasing=True, order=0)),
            pad_width=PAD_WIDTHS,
        )

        # not binary anymore
        rois += mask_t
        # care for overlaping rois

    if args.atlas_viewer is True:
        viewer.add_image(
            anatomical_stack_rs,
            interpolation3d="nearest",
            colormap="turbo",
        )
        viewer.add_image(
            filled_brain_mask, interpolation3d="nearest", colormap="viridis"
        )
        viewer.add_image(rois, interpolation3d="nearest", colormap="turbo")

    io.imsave(
        ATLAS_PATH + "/rois_atlas.tif",
        rois,
        check_contrast=False,
    )

    # atlas rois to polygons
    print("Converting atlas ROIs to polygons...")
    with mp.Pool(mp.cpu_count()) as pool:
        slice_region_dict = {}

        for slice in tqdm(range(n_slices)):
            region_dict = {}

            async_results = [
                pool.apply_async(
                    _convert_slice_region_to_multipolygons, args=(slice, r)
                )
                for r in SELECTED_REGIONS
            ]

            results = [arg.get() for arg in async_results]
            for i in results:
                region_dict[i["region"]] = i["polygons_list"]

            slice_region_dict[slice] = region_dict

        with open(os.path.join(ATLAS_PATH, "roi_shapes_dict.txt"), "w") as f:
            f.write(str(slice_region_dict))

        with open(os.path.join(ATLAS_PATH, "roi_shapes.json"), "w") as f:
            json.dump(slice_region_dict, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--atlas-viewer", action="store_true")
    parser.add_argument("--viewer", action="store_true")
    args = parser.parse_args()

    if args.viewer is True:
        viewer = napari.Viewer()

    # configure atlas dir
    shutil.rmtree(ATLAS_PATH, ignore_errors=True)
    os.makedirs(ATLAS_PATH)

    # configure temp dir
    shutil.rmtree(TEMP_PATH, ignore_errors=True)
    os.makedirs(TEMP_PATH)

    _assign_region_colors()
    _prepare_atlas()

    if args.viewer is True:
        napari.run()
