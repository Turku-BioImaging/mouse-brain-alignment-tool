# Meeting notes

brain_atlas_extraction.py -- atlas preparation
masks are rotated and then converted to dict.
centroid coordinates are in float.
rois_colors_dict.txt --> RGB values are in float.

preprocess_qt5.py
mainly for setting up UI

explore_args_z.py
padder outputs images 600x600 px.

conversion to tiff
currently implemented as fiji macro.

batch processing ideas

interactive_rois.py

known issue with transforming roi labels in napari

reduce point resolution of atlas rois

napari preferences, appearance was changed to increase the highlight thickness of shapes/points

possible to keep manually reshaped rois across the next image sets?

napari interface issues -- make "rois" layer automatically selected

excel file gets rewritten if napari is closed.

we need documentation!!!