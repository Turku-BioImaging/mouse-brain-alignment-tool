"""
This script preprocesses TIFF ARG images into separate images per animal and section. 
Modified from the original script `explore_args_Z.py`.
"""
import argparse
import os
import shutil

import numpy as np
from scipy import ndimage as ndi
from skimage import img_as_ubyte, io
from skimage.feature import peak_local_max
from skimage.filters import median, threshold_otsu
from skimage.measure import regionprops, regionprops_table
from skimage.morphology import binary_opening, remove_small_objects
from skimage.segmentation import watershed
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd

WORKDIR = os.path.join(os.path.dirname(__file__), "workdir")


def _check_image_file(image_path: str) -> bool:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file {image_path} does not exist.")
    if not image_path.endswith(".tif") and not image_path.endswith(".tiff"):
        raise ValueError(f"Image file {image_path} is not a TIFF file.")

    return True


def _configure_dirs(args):
    shutil.rmtree(WORKDIR, ignore_errors=True)
    os.makedirs(WORKDIR)

    image_basename = os.path.splitext(os.path.basename(args.image_path))[0]

    os.makedirs(os.path.join(WORKDIR, image_basename))
    os.makedirs(os.path.join(WORKDIR, image_basename, 'QC'))

    if args.num_animals == 2:
        animal_left_name = args.animal_left_name
        animal_right_name = args.animal_right_name

        for i in (animal_left_name, animal_right_name):
            os.makedirs(os.path.join(WORKDIR, image_basename, i, "sections"))
            os.makedirs(os.path.join(WORKDIR, image_basename, i, "tiff"))
    else:
        os.makedirs(os.path.join(WORKDIR, image_basename, "sections"))
        os.makedirs(os.path.join(WORKDIR, image_basename, "tiff"))


def _pad_section(img: np.ndarray, value: int):
    if img.shape[0] % 2 != 0:
        img = np.pad(img, pad_width=((0, 1), (0, 0)))
    if img.shape[1] % 2 != 0:
        img = np.pad(img, pad_width=((0, 0), (0, 1)))

    y = int((value - img.shape[0]) / 2)
    x = int((value - img.shape[1]) / 2)
    img = np.pad(img, pad_width=((y, y), (x, x)))

    return img


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--image-path", type=str, help="Path to the image file", required=True
    )
    parser.add_argument(
        "--num-slides", type=int, help="Number of slides", required=True
    )
    parser.add_argument(
        "--num-animals", type=int, help="Number of animals", required=True
    )
    parser.add_argument("--animal-left-name", type=str, help="Name of the left animal")
    parser.add_argument(
        "--animal-right-name", type=str, help="Name of the right animal"
    )
    parser.add_argument(
        "--output-dir", type=str, help="Output directory", required=True
    )
    parser.add_argument(
        "--with-napari", action="store_true", help="Enable napari for inspection"
    )

    args = parser.parse_args()

    if (args.with_napari) is True:
        import napari

        viewer = napari.Viewer()

    _check_image_file(args.image_path)
    _configure_dirs(args)

    # load image and identify large objects
    img = io.imread(args.image_path)
    blurred = median(img, np.ones((11, 11)))
    threshold_value = threshold_otsu(blurred)
    thresholded = blurred > threshold_value
    fill_holes = ndi.binary_fill_holes(thresholded)
    fill_holes = binary_opening(fill_holes, np.ones((5, 5)))
    large_objects_only = img_as_ubyte(remove_small_objects(fill_holes, 6000))

    if (args.with_napari) is True:
        viewer.add_image(img, name="img")
        viewer.add_image(blurred, name="blurred")
        viewer.add_image(large_objects_only, name="large_objects_only")

    # rotate the image parts
    sep_x_val = int(img.shape[1] / 2)
    if args.num_slides == 2:
        large_objects_only = np.hstack(
            (
                np.rot90(large_objects_only[:, 0:sep_x_val], 2),
                large_objects_only[:, sep_x_val:],
            )
        )

        img = np.hstack((np.rot90(img[:, 0:sep_x_val], 2), img[:, sep_x_val:]))

    large_objects_only = np.rot90(large_objects_only, 1)
    rotated_img = np.rot90(img, 1)

    if (args.with_napari) is True:
        viewer.add_image(rotated_img, name="rotated_img")

    # watershed segmentation
    distance = ndi.distance_transform_edt(large_objects_only)
    coords = peak_local_max(
        distance,
        footprint=np.ones((350, 350)),
        labels=large_objects_only,
        min_distance=200,
    )
    mask = np.zeros(distance.shape, dtype=bool)
    mask[tuple(coords.T)] = True
    markers, _ = ndi.label(mask)
    labels = watershed(-distance, markers=markers, mask=large_objects_only)

    # read region properties
    props = regionprops(label_image=labels, intensity_image=rotated_img)
    props_table = pd.DataFrame(regionprops_table(label_image=labels, intensity_image=rotated_img, properties=('label','centroid')))

    right = 0
    left = 0

    for i, p in enumerate(props):
        section = p.image_intensity
        section = _pad_section(section, 600)

        image_basename = os.path.splitext(os.path.basename(args.image_path))[0]
        sep_x_val = int(img.shape[1] / 2)

        if args.num_slides == 2:
            if p.centroid[0] < sep_x_val:
                if args.num_animals == 2:
                    fname = os.path.join(
                        args.animal_right_name,
                        "sections",
                        f"{args.animal_right_name}_{str(right).zfill(3)}.tif",
                    )
                else:
                    fname = os.path.join(
                        "sections", f"{image_basename}_1_{str(right).zfill(3)}.tif"
                    )
                right += 1
            else:
                if args.num_animals == 2:
                    fname = os.path.join(
                        args.animal_left_name,
                        "sections",
                        f"{args.animal_left_name}_{str(left).zfill(3)}.tif",
                    )
                else:
                    fname = os.path.join(
                        "sections", f"{image_basename}_2_{str(left).zfill(3)}.tif"
                    )
                left += 1
        else:
            fname = os.path.join("sections", f"{image_basename}_{str(i).zfill(3)}.tif")

        io.imsave(os.path.join(WORKDIR, image_basename, fname), section)

        props_table.loc[i, 'name'] = os.path.basename(fname).strip('.tif')

    # save raw image file
    image_basename = os.path.splitext(os.path.basename(args.image_path))[0]
    if args.num_animals == 2:
        left_fpath = os.path.join(
            WORKDIR,
            image_basename,
            args.animal_left_name,
            "tiff",
            f"{image_basename}.tif",
        )
        io.imsave(left_fpath, img)

        right_fpath = os.path.join(
            WORKDIR,
            image_basename,
            args.animal_right_name,
            "tiff",
            f"{image_basename}.tif",
        )
        io.imsave(right_fpath, img)
    else:
        fpath = os.path.join(WORKDIR, image_basename, "tiff", f"{image_basename}.tif")
        io.imsave(fpath, img)

    if (args.with_napari) is True:
        napari.run()


    font = {
            'color':  'black',
            'weight': 'bold',
            'size': 4
            }

    fig1, ax = plt.subplots(figsize=(10, 10), dpi=300)
    plt.imshow(io.imread(args.image_path), cmap="Greys")
    plt.title("Raw image")
    ax.set_rasterized(True)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)

    fig2, ax = plt.subplots(figsize=(10, 10), dpi=300)
    plt.imshow(rotated_img, cmap="Greys")
    plt.title("Rotated image")
    ax.set_rasterized(True)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)

    fig3, ax = plt.subplots(figsize=(10, 10), dpi=300)
    plt.imshow(rotated_img, cmap="Greys")
    plt.imshow(labels, cmap='rainbow', alpha=0.3*(labels>0))
    plt.title("Identified slices")
    ax.set_rasterized(True)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)

    for index, row in props_table.iterrows():
        plt.text(row['centroid-1'], row['centroid-0'], row['name'], 
                        ha='center', va='center', rotation=25, fontdict=font)
 

    pdfpath = os.path.join(WORKDIR, image_basename, "QC", 'processing_QC.pdf')
    pp = PdfPages(pdfpath) 
    pp.savefig(fig1)
    pp.savefig(fig2)
    pp.savefig(fig3) 
    pp.close()

    # move everything to selected output dir
    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir)
    workdir_contents = os.listdir(WORKDIR)
    for i in workdir_contents:
        source = os.path.join(WORKDIR, i)
        dest = os.path.join(args.output_dir, i)
        shutil.copytree(source, dest, dirs_exist_ok=True)
        
    shutil.rmtree(WORKDIR)
