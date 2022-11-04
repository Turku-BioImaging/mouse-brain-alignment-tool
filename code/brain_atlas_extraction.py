from bg_atlasapi import BrainGlobeAtlas, show_atlases
import os
import numpy as np
from skimage import io
from skimage.morphology import remove_small_objects
from skimage.measure import label, regionprops
from skimage.transform import rescale
from scipy import ndimage as ndi
import pandas as pd
from random import random
import rasterio
from rasterio import features
import shapely

"""    # not used anymore, now using shapely

def vectorize_regions(im: np.ndarray, threshold: float = 0.5):
    bin = im > threshold
    contours = measure.find_contours(bin, 0.5, fully_connected='high', positive_orientation='high')
    if len(contours) == 0:
        return contours
    approx_contours = []
    for contour in contours:
        contour = np.flip(contour, axis=1)
        approx_contours.append(measure.approximate_polygon(contour[:,[1,0]], 1).astype('uint').tolist())
    return approx_contours 

def vectorize_shaper(selected_atlas, region, slice):
    roi_t = BrainGlobeAtlas(selected_atlas).get_structure_mask(region)
    slice_t = roi_t[slice]
    slice_t = slice_t > 0
    slice_t=ndi.binary_fill_holes(slice_t).astype(slice_t.dtype)
    slice_t=remove_small_objects(slice_t)
    slice_t=ndi.binary_erosion(slice_t).astype(slice_t.dtype)
    slice_t = np.pad((rescale(slice_t, (4,4), anti_aliasing=False)), pad_width=((140,140), (72,72)))
    if region == "Isocortex": 
        # split isocortex shape in half
        slice_t[  : ,300] = 0
    polygon_t = vectorize_regions(slice_t)
    return polygon_t

"""

def mask_to_polygons(mask):
    all_polygons = []
    for shape, value in features.shapes(mask.astype(np.int16), mask=(mask >0), transform=rasterio.Affine(1.0, 0, 0, 0, 1.0, 0)):
        all_polygons.append(shapely.geometry.shape(shape))

    all_polygons = shapely.geometry.MultiPolygon(all_polygons)
    if not all_polygons.is_valid:
        all_polygons = all_polygons.buffer(0)
        if all_polygons.type == 'Polygon':
            all_polygons = shapely.geometry.MultiPolygon([all_polygons])
    return all_polygons

def shapely_shaper(selected_atlas, region, slice):
    roi_t = BrainGlobeAtlas(selected_atlas).get_structure_mask(region)
    slice_t = roi_t[slice]
    slice_t = slice_t > 0
    slice_t=ndi.binary_fill_holes(slice_t).astype(slice_t.dtype)
    slice_t=remove_small_objects(slice_t)
    slice_t=ndi.binary_erosion(slice_t).astype(slice_t.dtype)
    slice_t = np.pad((rescale(slice_t, (4,4), anti_aliasing=False)), pad_width=((140,140), (72,72)))
    if region == "Isocortex": 
        # split isocortex shape in half
        slice_t[  : ,300] = 0
    polygon_t = mask_to_polygons(slice_t)
    return polygon_t


def assign_region_colors(selected_regions, project_path):
    list_colors = []
    n = len(selected_regions)

    for i in range(n):
        r = random()
        g = random()
        b = random()
        rgba = [r,g,b,0.2]
        list_colors.append(rgba)

    roi_colors_dict = {selected_regions[a]: [a+1, list_colors[a]] for a,b in enumerate(selected_regions)}
    with open(project_path + "/atlas_files/rois_colors_dict.txt","w") as f:
        f.write( str(roi_colors_dict) )
    return roi_colors_dict


def prepare_atlas(atlas_name, region_list, project_path):
    
    bg_atlas = BrainGlobeAtlas(atlas_name) 
    #atlas_list = bg_atlas.lookup_df # list of abbreviations
    #pd.DataFrame(atlas_list).to_csv(project_path + '/atlas_files/rois_list.csv')

    ### anatomical atlas 
    anatomical_stack = bg_atlas.reference
    nslices = anatomical_stack.shape[0]
    anatomical_stack_rs = np.pad((rescale(anatomical_stack, (1,4,4), anti_aliasing=True)), pad_width=((0,0), (140,140), (72,72)))
    # to match 600,600 xy-shape and pixel size of images, values might be different for other atlases
    io.imsave(project_path + "/atlas_files/anatomical_atlas.tif", anatomical_stack_rs)

    ### atlas slices centroids
    brain_mask = bg_atlas.get_structure_mask(8)
    brain_mask = brain_mask/brain_mask.max()
    brain_mask = np.pad((rescale(brain_mask, (1,4,4), anti_aliasing=False)), pad_width=((0,0), (140,140), (72,72)))
    filled_brain_mask=ndi.binary_dilation(brain_mask).astype(brain_mask.dtype)
    for i in range(nslices):
        filled_brain_mask[i]=ndi.binary_fill_holes(filled_brain_mask[i]).astype(int)
    filled_brain_mask=ndi.binary_erosion(filled_brain_mask).astype(filled_brain_mask.dtype)
    slice_centers_dict = {}
    for i in range(nslices):
        props_atlas = regionprops(label(filled_brain_mask[i]))
        if len(props_atlas) > 0:
            center_of_mass_Atlas = props_atlas[0].centroid
            slice_centers_dict[i] = center_of_mass_Atlas
    with open(project_path + "/atlas_files/centroids_dict.txt","w") as f:
        f.write( str(slice_centers_dict) )

    ### regions of interest 
    rois = np.empty((nslices, 600, 600)) 
    for roi in region_list:
        mask_t = bg_atlas.get_structure_mask(roi)
        mask_t = np.pad((rescale(mask_t, (1,4,4), anti_aliasing=False)), pad_width=((0,0), (140,140), (72,72))) 
        # not binary anymore
        rois += mask_t 
        # care for overlaping rois
    io.imsave(project_path + "/atlas_files/rois_atlas.tif", rois)

    ### atlas rois to polygons 
    slice_reg_dict = {}
    for slice in range(nslices): # very long step
        reg_dict = {}
        for reg in region_list:
            reg_polygon = shapely_shaper(selected_atlas, reg, slice)
            polygons_list = []
            for poly in range(len(reg_polygon.geoms)):
                polygons_list.append((np.flip(np.array(reg_polygon[poly].exterior.coords).astype(np.int16), axis=1)).tolist())
                # probably easier way to save polygon as numpy array dirrectly from rasterio
            reg_dict[reg] = polygons_list
        slice_reg_dict[slice] = reg_dict
    with open(project_path + "/atlas_files/rois_shapes_dict.txt","w") as f:
        f.write( str(slice_reg_dict) )
    #df = pd.DataFrame(data = slice_reg_dict, index = region_list) 
    #df.to_csv(project_path + "/atlas_files/roi_shapes.csv", index=True)

        contours_s = []
        for i in polygon_t:
            poly = shapely.geometry.Polygon(i)
            poly_s = poly.simplify(tolerance=3)
            contours_s.append(np.array(poly_s.boundary.coords[:]))


atlas_path = "C:/Users/zuzka/Desktop/Finland_2022/ARR/"

if not os.path.exists(atlas_path + "atlas_files"):
    os.mkdir(atlas_path + 'atlas_files')

selected_atlas = "allen_mouse_100um"
selected_regions = ("CB", "MY", "P", "MB", "HY", "TH", "PAL", "STR", "OLF", "Isocortex", "HIP", "RHP", "CTXsp") 
# list of avilable abbreviations in 'rois_list.csv'

#show_atlases() # atlas alternatives

colors = assign_region_colors(selected_regions, atlas_path)
#prepare_atlas(selected_atlas, selected_regions, atlas_path)

print(colors)

