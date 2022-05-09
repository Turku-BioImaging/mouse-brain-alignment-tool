import os

# from skimage import io, img_as_uint
from skimage.filters import median, threshold_otsu
from skimage.morphology import remove_small_objects, binary_opening, binary_closing
import scipy.ndimage as ndi
import napari
import numpy as np
import cv2

viewer = napari.Viewer()

img = cv2.imread("arg/DPX91.tif", cv2.IMREAD_GRAYSCALE)

viewer.add_image(img, name="DPX71.tif", colormap="magma")

blurred = median(img, np.ones((11, 11)))

viewer.add_image(blurred, name="median_blur", colormap="magma")

threshold_value = threshold_otsu(blurred)
thresholded = blurred > threshold_value

viewer.add_image(thresholded, name="Otsu threshold")

fill_holes = ndi.binary_fill_holes(thresholded)
fill_holes = binary_opening(fill_holes, np.ones((5, 5)))
# fill_holes = binary_closing(fill_holes, np.ones((5, 5)))
viewer.add_image(fill_holes, name="fill_holes")

large_objects_only = remove_small_objects(fill_holes, min_size=5000)
viewer.add_image(large_objects_only, name="large_objects_only")
