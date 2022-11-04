from bg_atlasapi import BrainGlobeAtlas, show_atlases
import napari
import sys
import os
import numpy as np
from skimage import io, img_as_ubyte
from skimage.filters import median, threshold_otsu
from skimage.morphology import remove_small_objects, binary_opening, area_closing
from skimage.segmentation import watershed
from skimage.feature import peak_local_max
from skimage import measure
from skimage.measure import label, regionprops
from skimage.transform import rescale, resize, AffineTransform
from scipy import ndimage as ndi
from uuid import uuid4
import pandas as pd
from random import random
from magicgui import magicgui
import pathlib
from napari.layers import Image
import ast
import shapely
from shapely import geometry

def dir_loader(input_dir):
    global images_path, list_files, list_names
    project_path = input_dir
    images_path = project_path + "processed_images/"

    list_dir = os.listdir(images_path)
    list_files, list_names = [], []
    for file in list_dir:
        if file.endswith(".tif"):
            list_files.append(file)       
            list_names.append(file.rstrip(".tif"))

    df = pd.DataFrame(columns=regions_colnames, index = list_names)
    df.index.names = ['Images']
    df.to_csv(project_path + "results.csv", index=True)


def image_loader(image_number = 0):
    global imgfile, imgname, loaded_img
    imgfile = list_files[image_number]
    imgname = imgfile.rstrip(".tif")
    loaded_img = io.imread(images_path + imgfile)


def image_mask(imagefile):
    blurred = median(imagefile, np.ones((11, 11)))

    threshold_value = threshold_otsu(blurred)
    thresholded = blurred > threshold_value

    fill_holes = ndi.binary_fill_holes(thresholded)
    fill_holes = binary_opening(fill_holes, np.ones((5, 5)))

    large_objects_only = img_as_ubyte(remove_small_objects(fill_holes, min_size=6000))

    mask_img = label(large_objects_only)
    return mask_img


def align_centroids(imagefile):
    masked_img = image_mask(imagefile)
    selected_slice = int(roi_layer.position[0])
    center_of_mass_Atlas = centroids_dict[selected_slice]

    props_img = regionprops(label(masked_img))
    center_of_mass_Image = props_img[0].centroid

    # aligment of centroids
    #masked_img = np.roll(masked_img, -int(center_of_mass_Image[1]-center_of_mass_Atlas[1]), axis=1) 
    #masked_img = np.roll(masked_img, -int(center_of_mass_Image[0]-center_of_mass_Atlas[0]), axis=0)
    #new_props_img = regionprops(label(masked_img))
    #new_center_of_mass_Image = new_props_img[0].centroid
    image = np.roll(imagefile, -int(center_of_mass_Image[1]-center_of_mass_Atlas[1]), axis=1) 
    image = np.roll(imagefile, -int(center_of_mass_Image[0]-center_of_mass_Atlas[0]), axis=0)

    return image


def load_selected_rois(imagefile, simplification = 0):
    global selected_slice, shapes_layer
    selected_slice = int(roi_layer.position[0]) # get atlas slice position
    loaded_img = align_centroids(imagefile)
    viewer.grid.enabled = False
    viewer.layers.select_all()
    viewer.layers.remove_selected()

    viewer.add_image(loaded_img, name="image", colormap="gray_r")

    roi_names = []
    shapes_layer = viewer.add_shapes(
        opacity=0.4, 
        name='rois')

    for i,roi in enumerate(str_roi_list):
        polygon_t = (shapes_dict[selected_slice][roi])
        size = (len(polygon_t))
        polygon_s = simplify_polygons(polygon_t, simplification) # tolerance value
        if size > 0:
            roi_names.extend([roi]*size)
            shapes_layer.add_polygons(
                np.array(polygon_s, dtype=object),
                edge_width=2,
                edge_color='red',
                face_color=str_roi_list_dict[roi][1]
            )
    text_labels = {
        'string': roi_names, 'anchor': 'center', 'translation': [0, 0], 'size': 15,'color': 'black',
        }
    shapes_layer.text = text_labels
    #viewer.layers.select_next() # is there a way to select layer by name? 
    #viewer.layers[0].mode = "SELECT"

def simplify_polygons(input_polygon, tolerance_value):
    contours_s = []
    for shape in input_polygon:
        poly = shapely.geometry.Polygon(shape)
        poly_s = poly.simplify(tolerance=tolerance_value)
        contours_s.append(np.array(poly_s.boundary.coords[:]))
    return contours_s

def shape_transparency():
    selected = list(shapes_layer.selected_data)
    selected_names = shapes_layer.text.string.array[selected]
    color_array = []
    edge_color = []
    iter_t = 0
    for i in range(shapes_layer.nshapes):
        if i in selected:
            color_array.append(str_roi_list_dict[selected_names[iter_t]][1])
            edge_color.append([1.0,0.0,0.0,1.0])
            iter_t +=1
        else:
            color_array.append([0.0,0.0,0.0,0.0])
            edge_color.append([0.0,0.0,0.0,0.0])
    shapes_layer.face_color = color_array
    shapes_layer.edge_color = edge_color  #"transparent"


def polygon_to_roi():
    perserved_shapes  = list(shapes_layer.text.string.array)
    perserved_shapes_val = [str_roi_list_dict[item][0] for item in perserved_shapes]
    canvas_rect = np.array([[0,0],[599,599]])
    shapes_layer.add_rectangles(canvas_rect) # add rectangle to keep shape (600,600) of label layer
    labels_layer = shapes_layer.to_labels()
    shapes_layer.data = shapes_layer.data[0:(len(shapes_layer.data)-1)] # remove the new rectangle shape
    unique_labels = np.unique(labels_layer)

    new_labels_layer = np.zeros(labels_layer.shape, dtype=int)

    for i, val in enumerate(perserved_shapes_val):
        label_ind = unique_labels[i]
        array_t = (labels_layer == label_ind).astype(int)*val
        new_labels_layer += array_t
        
    return new_labels_layer


def roi_analyzer():
    r = polygon_to_roi()
    #viewer.add_labels(r)
    all_regions = r > 0
    areas = [sum(list(all_regions.flatten()))] # first value for all active rois
    means = [loaded_img[all_regions].mean()] # first value for all active rois
    bg_subtracted_means_per_pixel = [(means[0]-bg_mean if means[0]>bg_mean else 0)/areas[0]]
    for roi in str_roi_list:
        if str_roi_list_dict[roi][0] in list(np.unique(r)):
            region = r == str_roi_list_dict[roi][0]
            roi_mean = loaded_img[region].mean()
            means.append(roi_mean)
            area = sum(list(region.flatten()))
            areas.append(area)
            bg_subtracted_mean_per_pixel = (roi_mean-bg_mean if roi_mean>bg_mean else 0)/area
            bg_subtracted_means_per_pixel.append(bg_subtracted_mean_per_pixel)
        else:
            means.append(np.nan)
            areas.append(np.nan)
            bg_subtracted_means_per_pixel.append(np.nan)

    df_l = pd.read_csv(projectpath + "results.csv", index_col="Images")    
    df_l.loc[imgname,:] = bg_subtracted_means_per_pixel
    df_l.to_csv(projectpath + "results.csv", index=True)

    print("Analyzed!")
    print()


def select_background(project_path):
    global y,x, arg_scan, bg_layer, bg_dock
    arg_scan_dir_path = project_path + "tif_file/"
    arg_scan_name = [g for g in os.listdir(arg_scan_dir_path) if g.endswith("tif")][0]
    arg_scan = io.imread(arg_scan_dir_path+arg_scan_name)
    y,x = int(arg_scan.shape[0]), int(arg_scan.shape[1])
    rect_y,rect_x = int(y/2)-400,int(x/2)-200
    whole_image_layer = viewer.add_image(arg_scan, name="image_scan", colormap="gray_r", contrast_limits=[0, np.max(arg_scan)])
    bg_layer = viewer.add_shapes(opacity=0.4, name='background_area')
    bg_rect = np.array([[rect_y,rect_x],[rect_y+800,rect_x+400]])
    bg_layer.add_rectangles(bg_rect, edge_width=10, edge_color='red', face_color='orange')
    bg_dock = viewer.window.add_dock_widget([bg_widget, start_alignment])
    print()
    print()
    print("Select background area.")

def get_background():
    canvas_rect = np.array([[0,0],[y-1,x-1]])
    bg_layer.add_rectangles(canvas_rect) # to keep shape image layer
    bg_labels = bg_layer.to_labels()
    bg_layer.data = bg_layer.data[0:(len(bg_layer.data)-1)]
    mean = arg_scan[bg_labels == 1].mean()
    return mean

def initialize_analysis_tool():
    global roi_layer, image_layer
    viewer.grid.enabled = True
    viewer.grid.shape = (1,-1)
    bg_dock.hide() # removal was giving error
    atlas_layer = viewer.add_image(
        anatomical_stack_rs,
        name="anatomical_stack",
        contrast_limits=[0, np.max(anatomical_stack_rs)],
    )
    roi_layer = viewer.add_image(rois, name="atlas_rois", 
        colormap = "magma",
        contrast_limits=[0, np.max(rois)])
    image_layer = viewer.add_image(loaded_img, name="image", colormap="gray_r")
    viewer.window.add_dock_widget([atlas_view, rois_widget, simple_rois_widget, hide_widget, analyze_widget, next_image, previous_image])
    viewer.reset_view()

@magicgui(call_button='Calculate bg')
def bg_widget():
    global bg_mean
    bg_mean = 0
    bg_mean = get_background()
    print("Background mean is :", bg_mean)

@magicgui(call_button='Start alignment')
def start_alignment():
    viewer.layers.select_all()
    viewer.layers.remove_selected()
    initialize_analysis_tool()

@magicgui(call_button='Add rois / Reset')
def rois_widget():
    load_selected_rois(loaded_img)

@magicgui(call_button='Simplify rois')
def simple_rois_widget():
    load_selected_rois(loaded_img, 4)

@magicgui(call_button='Hide unselected rois')
def hide_widget():
    shape_transparency()

@magicgui(call_button='Analyze rois')
def analyze_widget():
    roi_analyzer()

@magicgui(call_button='Brain Atlas')
def atlas_view():
    global roi_layer
    viewer.grid.enabled = True
    viewer.grid.shape = (1,-1)
    viewer.layers.select_all()
    viewer.layers.remove_selected()
    atlas_layer = viewer.add_image(
        anatomical_stack_rs,
        name="anatomical_stack",
        contrast_limits=[0, np.max(anatomical_stack_rs)],
    )
    roi_layer = viewer.add_image(rois, name="atlas_rois", 
        colormap = "magma",
        contrast_limits=[0, np.max(rois)])
    image_layer = viewer.add_image(loaded_img, name="image", colormap="gray_r")
    viewer.reset_view()

@magicgui(call_button="Next image")
def next_image():
    global loaded_img
    selected_slice = int(roi_layer.position[0]) # get atlas slice position
    actual = list_names.index(imgname)
    if actual == len(list_names):
        pass
    else:
        image_loader(actual+1)
        viewer.layers.remove("image")
        loaded_img = align_centroids(loaded_img)
        image_layer = viewer.add_image(loaded_img, name="image", colormap="gray_r")
        if len(viewer.layers) == 3: # when brain atlas view is on
            pass
        else:
            viewer.layers.reverse()
        print(imgname)
    #viewer.layers.select_previous()
    #viewer.layers[0].mode = "SELECT"
        
@magicgui(call_button="Previous image")
def previous_image():
    global loaded_img
    selected_slice = int(roi_layer.position[0]) # get atlas slice position
    actual = list_names.index(imgname)
    if actual == 0:
        pass
    else:
        image_loader(actual-1)
        viewer.layers.remove("image")
        loaded_img = align_centroids(loaded_img)
        image_layer = viewer.add_image(loaded_img, name="image", colormap="gray_r")
        if len(viewer.layers) == 3: # when brain atlas view is on
            pass
        else:
            viewer.layers.reverse()
        print(imgname)
    #viewer.layers.select_previous()
    #viewer.layers[0].mode = "SELECT"

### paths
projectpath = sys.argv[1] + "/"
atlaspath = "C:/Users/zuzka/Desktop/Finland_2022/ARR/" # to be specified to working directory

### loading atlas info
anatomical_stack_rs = io.imread(atlaspath + "atlas_files/anatomical_atlas.tif")
rois = io.imread(atlaspath + "atlas_files/rois_atlas.tif")

with open(atlaspath+"atlas_files/rois_colors_dict.txt") as f:
    data = f.read()
str_roi_list_dict = ast.literal_eval(data)
str_roi_list = list(str_roi_list_dict.keys())
regions_colnames = ["All_rois"] + list(str_roi_list)

with open(atlaspath+"atlas_files/centroids_dict.txt") as f:
    data = f.read()
centroids_dict = ast.literal_eval(data)

with open(atlaspath+"atlas_files/rois_shapes_dict.txt") as f:
    data = f.read()
shapes_dict = ast.literal_eval(data)

### loading directory and initialize napari
dir_loader(projectpath)
image_loader()

viewer = napari.Viewer()
viewer.window.resize(1600,800)

select_background(projectpath)

napari.run()
