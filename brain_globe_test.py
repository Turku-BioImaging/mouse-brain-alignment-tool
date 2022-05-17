from bg_atlasapi import BrainGlobeAtlas, show_atlases
from matplotlib import pyplot as plt
import napari
import numpy as np

show_atlases()

bg_atlas = BrainGlobeAtlas("allen_mouse_100um")
bg_atlas.metadata

anatomical_stack = bg_atlas.reference
annotation_stack = bg_atlas.annotation
hemispheres_stack = bg_atlas.hemispheres

viewer = napari.Viewer()
viewer.add_image(
    anatomical_stack,
    name="anatomical_stack",
    contrast_limits=[0, np.max(anatomical_stack)],
)
viewer.add_image(annotation_stack, name="annotation_stack", contrast_limits=[0, 25000], colormap='viridis')
viewer.add_image(
    hemispheres_stack,
    name="hemispheres_stack",
    contrast_limits=[0, np.max(hemispheres_stack)],
)

annotation_stack.dtype

# get some structures
bg_atlas.structures["CTX"]
mask = bg_atlas.get_structure_mask(549)
viewer.add_image(mask, name="thalamus")
