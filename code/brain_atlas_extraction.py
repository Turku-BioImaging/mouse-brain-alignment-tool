import os
import numpy as np
import shutil
import shapely
import random
import napari
import argparse
import pandas as pd

from bg_atlasapi import BrainGlobeAtlas as bga
from skimage import io, img_as_uint
from skimage.morphology import remove_small_objects
from skimage.measure import label, regionprops
from skimage.transform import rescale
from rasterio import features, Affine
from scipy import ndimage as ndi
from tqdm import tqdm


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

viewer = None


def mask_to_polygons(mask):
    all_polygons = []
    for shape, value in features.shapes(
        mask.astype(np.int16),
        mask=(mask > 0),
        transform=Affine(1.0, 0, 0, 0, 1.0, 0),
    ):
        all_polygons.append(shapely.geometry.shape(shape))

    all_polygons = shapely.geometry.MultiPolygon(all_polygons)
    if not all_polygons.is_valid:
        all_polygons = all_polygons.buffer(0)
        if all_polygons.type == "Polygon":
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
        (rescale(slice_t, (4, 4), anti_aliasing=False)),
        pad_width=((140, 140), (72, 72)),
    )
    if region == "Isocortex":
        # split isocortex shape in half
        slice_t[:, 300] = 0
    polygon_t = mask_to_polygons(slice_t)
    return polygon_t


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

    # to match 600,600 xy-shape and pixel size of images, values might be different for other atlases
    io.imsave(
        ATLAS_PATH + "/anatomical_atlas.tif", anatomical_stack_rs, check_contrast=False
    )

    # atlas slices centroids
    brain_mask = bg_atlas.get_structure_mask(8)  # dtype np.uint32

    # brain_mask = brain_mask / brain_mask.max()
    brain_mask = np.pad(
        (rescale(brain_mask, (1, 4, 4), anti_aliasing=True, order=0)),
        pad_width=((0, 0), (140, 140), (72, 72)),
    )

    filled_brain_mask = ndi.binary_dilation(brain_mask)

    for i in range(n_slices):
        filled_brain_mask[i] = ndi.binary_fill_holes(filled_brain_mask[i])

    filled_brain_mask = ndi.binary_erosion(filled_brain_mask)

    if args.viewer == True:
        viewer.add_image(
            anatomical_stack_rs,
            interpolation3d="nearest",
            colormap="turbo",
        )
        viewer.add_image(brain_mask, interpolation3d="nearest", colormap="turbo")
        viewer.add_image(
            filled_brain_mask, interpolation3d="nearest", colormap="viridis"
        )

    # slice_centers_dict = {}
    slice_centroids = []
    for i in range(n_slices):
        props_atlas = regionprops(label(filled_brain_mask[i]))
        if len(props_atlas) > 0:
            center_of_mass_atlas = props_atlas[0].centroid

            slice_centroids.append({"slice": i, "centroid": center_of_mass_atlas})

    df = pd.DataFrame(slice_centroids)
    df.to_csv(f"{ATLAS_PATH}/slice_centroids.csv", index=False)

    # # get regions of interest
    # rois = np.empty((nslices, 600, 600))
    # for roi in SELECTED_REGIONS:
    #     mask_t = bg_atlas.get_structure_mask(roi)
    #     mask_t = np.pad(
    #         (rescale(mask_t, (1, 4, 4), anti_aliasing=False)),
    #         pad_width=((0, 0), (140, 140), (72, 72)),
    #     )
    #     # not binary anymore
    #     rois += mask_t
    #     # care for overlaping rois

    # io.imsave(
    #     ATLAS_PATH + "/rois_atlas.tif",
    #     rois,
    #     check_contrast=False,
    # )

    # # atlas rois to polygons
    # print("Converting atlas ROIs to polygons...")
    # slice_reg_dict = {}
    # for slice in tqdm(range(nslices)):  # very long step
    #     reg_dict = {}
    #     for reg in SELECTED_REGIONS:
    #         reg_polygon = shapely_shaper(reg, slice)
    #         polygons_list = []
    #         for poly in range(len(reg_polygon.geoms)):
    #             polygons_list.append(
    #                 (
    #                     np.flip(
    #                         np.array(reg_polygon[poly].exterior.coords).astype(
    #                             np.int16
    #                         ),
    #                         axis=1,
    #                     )
    #                 ).tolist()
    #             )
    #             # probably easier way to save polygon as numpy array dirrectly from rasterio
    #         reg_dict[reg] = polygons_list
    #     slice_reg_dict[slice] = reg_dict
    # with open(ATLAS_PATH + "/rois_shapes_dict.txt", "w") as f:
    #     f.write(str(slice_reg_dict))
    #     # df = pd.DataFrame(data = slice_reg_dict, index = region_list)
    #     # df.to_csv(project_path + "/atlas_files/roi_shapes.csv", index=True)

    #     contours_s = []
    #     for i in polygon_t:
    #         poly = shapely.geometry.Polygon(i)
    #         poly_s = poly.simplify(tolerance=3)
    #         contours_s.append(np.array(poly_s.boundary.coords[:]))


# atlas_path = "C:/Users/zuzka/Desktop/Finland_2022/ARR/"

# if not os.path.exists(atlas_path + "atlas_files"):
#     os.mkdir(atlas_path + "atlas_files")

# selected_atlas = "allen_mouse_100um"
# selected_regions = (
#     "CB",
#     "MY",
#     "P",
#     "MB",
#     "HY",
#     "TH",
#     "PAL",
#     "STR",
#     "OLF",
#     "Isocortex",
#     "HIP",
#     "RHP",
#     "CTXsp",
# )
# # list of avilable abbreviations in 'rois_list.csv'

# # show_atlases() # atlas alternatives

# colors = assign_region_colors(selected_regions, atlas_path)
# # prepare_atlas(selected_atlas, selected_regions, atlas_path)

# print(colors)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--viewer", action="store_true")
    args = parser.parse_args()

    if args.viewer == True:
        viewer = napari.Viewer()

    # configure atlas dir
    shutil.rmtree(ATLAS_PATH, ignore_errors=True)
    os.makedirs(ATLAS_PATH)

    _assign_region_colors()
    _prepare_atlas()

    if args.viewer == True:
        napari.run()
