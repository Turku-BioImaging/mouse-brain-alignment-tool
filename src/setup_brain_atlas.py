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

import argparse
import json
import multiprocessing as mp
import os
import random

import numpy as np
import pandas as pd
import shapely
from bg_atlasapi import BrainGlobeAtlas as bga
from rasterio import Affine, features
from scipy import ndimage as ndi
from skimage import io
from skimage.measure import label, regionprops
from skimage.morphology import remove_small_objects
from skimage.transform import rescale
from tqdm import tqdm

ATLAS_PATH = os.path.join(os.path.dirname(__file__), "brain_atlas_files")
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


def _check_files():
    if not os.path.isfile(os.path.join(ATLAS_PATH, "roi_colors.json")):
        return False

    if not os.path.isfile(os.path.join(ATLAS_PATH, "slice_centroids.csv")):
        return False

    if not os.path.isfile(os.path.join(ATLAS_PATH, "roi_shapes.json")):
        return False

    print("All text data files found.")
    return True


def _check_tiff_files():
    if not os.path.isfile(os.path.join(ATLAS_PATH, "anatomical_atlas.tif")):
        return False

    if not os.path.isfile(os.path.join(ATLAS_PATH, "rois_atlas.tif")):
        return False

    print("Atlas TIFFs found.")
    return True


def _save_rois_to_tiff(n_slices: int, bg_atlas: bga):
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

    io.imsave(os.path.join(ATLAS_PATH, "rois_atlas.tif"), rois, check_contrast=False)


def _save_slice_centroids(bg_atlas: bga, n_slices: int):
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
        props_atlas = regionprops(label(brain_mask[i]))
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


def _save_roi_shapes(n_slices: int):
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

        with open(os.path.join(ATLAS_PATH, "roi_shapes.json"), "w") as f:
            json.dump(slice_region_dict, f)


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

    with open(os.path.join(ATLAS_PATH, "roi_colors.json"), "w") as f:
        json.dump(roi_colors_dict, f)


def _convert_to_multipolygon(mask: np.ndarray):
    shape_results = []

    for shape, _ in features.shapes(
        mask.astype(np.int16),
        mask=(mask > 0),
        transform=Affine(1.0, 0, 0, 0, 1.0, 0),
    ):
        shape_results.append(shapely.geometry.shape(shape))

    polygons = []
    for item in shape_results:
        if item.geom_type == "Polygon":
            polygons.append(item)
        elif item.geom_type == "MultiPolygon":
            for i in item:
                polygons.append(i)

    # simplify the polygons to reduce vertices
    simplified_polygons = []
    for poly in polygons:
        simplified_polygons.append(poly.simplify(tolerance=4))

    multi_polygon = shapely.geometry.MultiPolygon(simplified_polygons)
    return multi_polygon


def _shapely_shaper(region, slice):
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

    polygon = _convert_to_multipolygon(slice_t)

    return polygon


def _convert_slice_region_to_multipolygons(slice: int, region: str):
    region_polygon = _shapely_shaper(region, slice)

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

    print({"region": region, "polygons_list": polygons_list})
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

    if args.force_download is True or _check_tiff_files() is False:
        io.imsave(
            os.path.join(ATLAS_PATH, "anatomical_atlas.tif"),
            anatomical_stack_rs,
            check_contrast=False,
        )

    if args.force_download is True or _check_tiff_files() is False:
        _save_rois_to_tiff(n_slices=n_slices, bg_atlas=bg_atlas)

    if args.force_download is True or _check_files() is False:
        _assign_region_colors()

    if args.force_download is True or _check_files() is False:
        _save_roi_shapes(n_slices=n_slices)

    if args.force_download is True or _check_files() is False:
        _save_slice_centroids(bg_atlas=bg_atlas, n_slices=n_slices)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-download", action="store_true")
    args = parser.parse_args()

    # configure atlas dir
    if not os.path.isdir(ATLAS_PATH):
        os.makedirs(ATLAS_PATH)

    _prepare_atlas()
