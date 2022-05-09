import os
from skimage import io, img_as_uint
from skimage.filters import median, threshold_otsu
import napari
import numpy as np
import cv2

viewer = napari.Viewer()

img = cv2.imread("arg/DPX71.tif", cv2.IMREAD_GRAYSCALE)

viewer.add_image(img, name="DPX71.tif", colormap="magma")

blurred = median(img, np.ones((7, 7)))

viewer.add_image(blurred, name="median_blur", colormap="magma")

threshold_value = threshold_otsu(blurred)
thresholded = blurred > threshold_value

viewer.add_image(thresholded, name="Otsu threshold")
