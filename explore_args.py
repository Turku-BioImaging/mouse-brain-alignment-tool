from skimage import io, img_as_ubyte
from skimage.filters import median, threshold_otsu
from skimage.morphology import remove_small_objects
from skimage.segmentation import watershed
from skimage.feature import peak_local_max
from scipy import ndimage as ndi
import napari
import numpy as np


viewer = napari.Viewer()

img = io.imread("arg/DPX91.tif")
viewer.add_image(img, name="DPX91.tif", contrast_limits=(0, 65535), colormap="magma")

blurred = median(img, np.ones((11, 11)))
viewer.add_image(
    blurred, name="median_blur", colormap="magma", contrast_limits=(0, 65535)
)

threshold_value = threshold_otsu(blurred)
thresholded = blurred > threshold_value
viewer.add_image(thresholded, name="Otsu threshold")

fill_holes = ndi.binary_fill_holes(thresholded)
viewer.add_image(fill_holes, name="fill_holes")

large_objects_only = img_as_ubyte(remove_small_objects(fill_holes, min_size=6000))
viewer.add_image(large_objects_only, name="large_objects_only")

# watershed segmentation
distance = ndi.distance_transform_edt(large_objects_only)
coords = peak_local_max(
    distance, footprint=np.ones((300, 300)), labels=large_objects_only
)
mask = np.zeros(distance.shape, dtype=bool)
mask[tuple(coords.T)] = True
markers, _ = ndi.label(mask)
labels = watershed(-distance, markers=markers, mask=large_objects_only)

viewer.add_image(
    labels, name="watershed", contrast_limits=(0, labels.max()), colormap="viridis"
)
