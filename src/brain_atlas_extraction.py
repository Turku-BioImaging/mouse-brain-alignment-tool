import os
import numpy as np
import shutil
import shapely
import random
import napari
import argparse
import uuid
import pandas as pd

from bg_atlasapi import BrainGlobeAtlas as bga
from skimage import io, img_as_uint, img_as_ubyte
from skimage.morphology import remove_small_objects
from skimage.measure import label, regionprops
from skimage.transform import rescale
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

    # print(len(all_polygons))
    all_polygons = shapely.geometry.MultiPolygon(all_polygons)
    if not all_polygons.is_valid:
        all_polygons = all_polygons.buffer(0)
    if all_polygons.geom_type == "Polygon":
        all_polygons = shapely.geometry.MultiPolygon([all_polygons])
    return all_polygons


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

    # slice_t = slice_t > 0
    # slice_t = ndi.binary_fill_holes(slice_t)
    # slice_t = remove_small_objects(slice_t)
    # slice_t = np.pad(
    #     (rescale(slice_t, (4, 4), anti_aliasing=False, order=0)),
    #     pad_width=((140, 140, 72, 72)),
    # )

    # return slice_t

    if region == "Isocortex":
        # split isocortex shape in half
        slice_t[:, 300] = 0
    polygon = mask_to_polygons(slice_t)
    return polygon


def _assign_region_colors():
    list_colors = []
    n = len(SELECTED_REGIONS)

    for i in range(n):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        rgba = [r, g, b, 0.2]
        list_colors.append(rgba)

    roi_colors_dict = {
        SELECTED_REGIONS[a]: [a + 1, list_colors[a]]
        for a, b in enumerate(SELECTED_REGIONS)
    }
    with open(ATLAS_PATH + "/roi_colors_dict.txt", "w") as f:
        f.write(str(roi_colors_dict))


def _prepare_atlas():

    bg_atlas = bga(SELECTED_ATLAS)
    # atlas_list = bg_atlas.lookup_df # list of abbreviations
    # pd.DataFrame(atlas_list).to_csv(project_path + '/atlas_files/rois_list.csv')

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
        ATLAS_PATH + "/anatomical_atlas.tif", anatomical_stack_rs, check_contrast=False
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

    # slice_centers_dict = {}
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
    df.to_csv(f"{ATLAS_PATH}/slice_centroids.csv", index=False)

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
    slice_reg_dict = {}
    for slice in tqdm(range(n_slices)):  # very long step
        reg_dict = {}
        for region in SELECTED_REGIONS:
            region_polygon = shapely_shaper(region, slice)

            polygons_list = []

            if len(region_polygon.geoms) > 0:

                # for i in range(len(region_polygon.geoms)):
                #     print(region_polygon.geoms[i])

                for polygon in region_polygon.geoms:
                    polygons_list.append(
                        (
                            np.flip(
                                np.array(polygon.exterior.coords).astype(np.int16),
                                axis=1,
                            )
                        ).tolist()
                    )

                # for i in range(len(region_polygon.geoms)):
                # print(region_polygon.geoms[i].coords)
                # polygons_list.append(
                #     (
                #         np.flip(
                #             np.array(region_polygon[poly].exterior.coords).astype(
                #                 np.int16
                #             ),
                #             axis=1,
                #         )
                #     ).tolist()
                # )
                # probably easier way to save polygon as numpy array dirrectly from rasterio

            print(polygons_list)
        #     reg_dict[region] = polygons_list
        # slice_reg_dict[slice] = reg_dict
        # break
    # with open(ATLAS_PATH + "/rois_shapes_dict.txt", "w") as f:
    #     f.write(str(slice_reg_dict))

    #     # contours_s = []
    #     # for i in polygon_t:
    #     #     poly = shapely.geometry.Polygon(i)
    #     #     poly_s = poly.simplify(tolerance=3)
    #     #     contours_s.append(np.array(poly_s.boundary.coords[:]))


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
