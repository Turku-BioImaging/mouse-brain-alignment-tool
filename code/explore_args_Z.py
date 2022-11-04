import os
import sys
from skimage import io, img_as_ubyte
from skimage.filters import median, threshold_otsu
from skimage.morphology import remove_small_objects, binary_opening
from skimage.segmentation import watershed
from skimage.feature import peak_local_max
from skimage.measure import regionprops, label
from scipy import ndimage as ndi
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as img
from matplotlib.backends.backend_pdf import PdfPages

def padder(input_image, value):
    if input_image.shape[0]%2 != 0:
        input_image = np.pad(input_image, pad_width=((0,1), (0,0)))
    if section.shape[1]%2 != 0:
        input_image = np.pad(input_image, pad_width=((0,0), (0,1)))
    y = int((value-input_image.shape[0])/2)
    x = int((value-input_image.shape[1])/2)
    input_image = np.pad(input_image, pad_width=((y,y), (x,x)))
    return input_image

dir_path = os.path.dirname(sys.argv[1]) + "/"
projectpath = sys.argv[1] + "/"
numslides = sys.argv[2]
numanimals = sys.argv[3]

if numanimals == "2":
    import shutil
    animalR = sys.argv[4]
    animalL = sys.argv[5]
    for animal in (animalR, animalL):
        os.mkdir(dir_path + animal)
        os.mkdir(dir_path + animal + '/processed_images')
        os.mkdir(dir_path + animal + '/tif_file')
else:
    if not os.path.exists(projectpath + "processed_images"):
        os.mkdir(projectpath + 'processed_images')

# add convesion of raw to tif and save it to new tif_file folder
imgpath = projectpath + "tif_file/"
imgfile = [g for g in os.listdir(imgpath) if g.endswith("tif")][0] # load tif
#imgname = imgfile.rstrip(".tif")
imgname = os.path.basename(os.path.normpath(projectpath))


print('Copied')
print()
print()
print("File name: ", imgname)
print("Number of slides: ", numslides)
print("Number of animals: ", numanimals)
if numanimals == "2":
    print("Animals: ", animalR, ",",animalL)
print()
print()
print("Running preprocessing...")


if __name__ == '__main__':

    raw_img = io.imread(imgpath+imgfile)
    img = raw_img

    blurred = median(img, np.ones((11, 11)))

    threshold_value = threshold_otsu(blurred)
    thresholded = blurred > threshold_value

    fill_holes = ndi.binary_fill_holes(thresholded)
    fill_holes = binary_opening(fill_holes, np.ones((5, 5)))

    large_objects_only = img_as_ubyte(remove_small_objects(fill_holes, min_size=6000))

    # rotation of image parts
    sep_x_val = int(img.shape[1]/2)
    if numslides == "2":
        large_objects_only = np.hstack((np.rot90(large_objects_only[:,0:sep_x_val], 2),large_objects_only[:,sep_x_val:]))
        img = np.hstack((np.rot90(img[:,0:sep_x_val], 2),img[:,sep_x_val:]))
    large_objects_only = np.rot90(large_objects_only, 1)
    img = np.rot90(img,1)
    rotated_img = img

    # watershed segmentation
    distance = ndi.distance_transform_edt(large_objects_only)
    coords = peak_local_max(
        distance, 
        footprint=np.ones((350, 350)), #changed value to 350 
        labels=large_objects_only, 
        min_distance = 200 #added minimal distance to avoid cuting one slice into parts
    )
    mask = np.zeros(distance.shape, dtype=bool)
    mask[tuple(coords.T)] = True
    markers, _ = ndi.label(mask)
    labels = watershed(-distance, markers=markers, mask=large_objects_only)

    # read region properties
    props = regionprops(label_image=labels, intensity_image=img)
    props

r,l = 0,0
for i,p in enumerate(props):
    section = p.image_intensity
    section = padder(section, 600)
    subfolder=imgname
    if numslides == "2":
        if p.centroid[0] < sep_x_val:
            if numanimals == "2":
                fname = animalR + "_" + str(r).zfill(3) + ".tif"
                subfolder = animalR+"/"
            else:
                fname = imgname + "_1_" + str(r).zfill(3) + ".tif"
            r += 1
        else:
            if numanimals == "2":
                fname = animalL + "_" + str(l).zfill(3) + ".tif"
                subfolder = animalL+"/"
            else:
                fname = imgname + "_2_" + str(l).zfill(3) + ".tif"
            l += 1
    else:
        fname = imgname + "_" + str(i).zfill(3) + ".tif"
    io.imsave(dir_path+subfolder+f"processed_images/{fname}", section)

if numanimals == "2":
    dst_path1 = dir_path + animalR + '/tif_file/'
    dst_path2 = dir_path + animalL + '/tif_file/'
    print(dst_path1)
    io.imsave(dst_path1+imgfile, raw_img)
    io.imsave(dst_path2+imgfile, raw_img)

print()
print()
print("Finished preprocessing.")
print()
print()
print("Creating QC file...")

font = {
        'color':  'black',
        'weight': 'bold',
        'size': 4
        }

fig1, ax = plt.subplots()
plt.imshow(raw_img, cmap="Greys")
plt.title("Raw image")
ax.set_rasterized(True)
ax.get_xaxis().set_visible(False)
ax.get_yaxis().set_visible(False)

fig2, ax = plt.subplots()
plt.imshow(rotated_img, cmap="Greys")
plt.title("Rotated image")
ax.set_rasterized(True)
ax.get_xaxis().set_visible(False)
ax.get_yaxis().set_visible(False)

fig3, ax = plt.subplots()
plt.imshow(img, cmap="Greys") #interpolation='none'
plt.imshow(labels, cmap='rainbow', alpha=0.3*(labels>0)) #interpolation='none'
plt.title("Identified slices")

r,l = 0,0
for i,p in enumerate(props):
    if numslides == "2":
        if p.centroid[0] < sep_x_val:
            if numanimals == "2":
                plt.text(int(p.centroid[1]),int(p.centroid[0]), animalR + "_" + str(r).zfill(3), 
                    horizontalalignment='center', verticalalignment='center', fontdict=font)
            else:
                plt.text(int(p.centroid[1]),int(p.centroid[0]), "1_" + str(r).zfill(3), 
                    horizontalalignment='center', verticalalignment='center', fontdict=font)
            r+=1
        else:
            if numanimals == "2":
                plt.text(int(p.centroid[1]),int(p.centroid[0]), animalL + "_" + str(l).zfill(3), 
                    horizontalalignment='center', verticalalignment='center', fontdict=font)
            else:
                plt.text(int(p.centroid[1]),int(p.centroid[0]), "2_" + str(l).zfill(3), 
                    horizontalalignment='center', verticalalignment='center', fontdict=font)
            l+=1
    else:
        plt.text(int(p.centroid[1]),int(p.centroid[0]), str(i).zfill(3), 
            horizontalalignment='center',
            verticalalignment='center',
            fontdict=font)

ax.set_rasterized(True)
ax.get_xaxis().set_visible(False)
ax.get_yaxis().set_visible(False)

pp = PdfPages(projectpath + 'processing_QC.pdf') 
pp.savefig(fig1)
pp.savefig(fig2)
pp.savefig(fig3) 
pp.close()

print()
print()
print("Finished!")
