# User Documentation
Download a copy of the latest release through the [GitHub repository](https://github.com/Turku-BioImaging/mouse-brain-alignment-tool/releases) hosted by Turku BioImaging. Download and extract the release ZIP file into a folder of your choice. After extraction, there should be three files present:
- preprocess-*version-number*.exe
- analyze-*version-number*.exe
- data.xlsx

## Module 1 - Preprocessing
First here: how to set up images and excel.

### Input data
A single folder is required as input. This folder must contain any number of TIFF images and a single _data.xlsx_ file. Images must use the extension _*.tif_, otherwise they will not be included in the preprocessing. The _data.xlsx_ is an Excel workbook that must follow a particular format. It includes the folowing columns: 
- image_filename
- num_slides
- num_animals
- animal_left_name
- animal_right_name

<br/><br/>
<figure>
  <img src="/assets/docs/screenshot-102249.png" alt="Example of Excel data file" style="width: 50%; height: auto;">
  <figcaption>Example of Excel data file</figcaption>
</figure>
  
<br/><br/>
<figure>
  <img src="/assets/docs/screenshot-102625.png" alt="Example contents of input folder" style="width: 50%; height: auto;">
  <figcaption>Example contents of input folder</figcaption>
</figure>
  
<br/><br/>
For every image, if the column *num_animals* has a value of _1_, then the columns *animal_left_name* and *animal_right_name* must be blank. A copy of the Excel template is located [here](excel_template.xlsx).

### Expected output

### Usage
Double-click on __preprocess-0.2.0.exe__ to open the preprocessing interface (this can take up to a minute). After the preprocess window is open, select the source directory (the folder containing images and the prepared Excel sheet _data.xlsx_). Select the output directory, as where do you wish the preprocessed data to be saved to. Click run to start the preprocess.  
__IMPORTANT:__ The Excel document should not be open while the preprocess app is running!

------
<img width="317" alt="preprocess_gui" src="https://github.com/Turku-BioImaging/mouse-brain-alignment-tool/assets/136598378/581beab6-5ac6-47db-8922-45bfb86e914a">  
Select the directory where your images and data.xls file are. Select the folder where you want the preprocessed images to appear as output directory.
Depending on data size, the preprocess can take longer time. Process can be tracked from running log, where all processed images will be marked, as well as the completion of preprocessing. 
In the output folder, there will be a separate folder for each image, with a name corresponding to image_filename. The folder will contain separate subfolders for each animal in the image. These subfolders will contain sections folder, the tiff folder that contains original .tif file as well as QC folder. Sections folder contains all the sections of the brain as separate .tif files, while QC (quality control) folder contains a PDF document with raw image, rotated slices and documented slices. 

## Module 2 - Analysis
This module provides a graphical interface where preprocessed ARG brain sections can be matched to anatomical atlas sections and their intensity analyzed. Regions-of-interest (ROIs) pertaining to specific brain regions from the anatomical atlas can be manually registered to fit the ARG image. Average intensities of individual ROIs can then be measured and saved in a data file.

There is no need for the user to analyze all image sections. Analyzed data is stored in a CSV data file that is automatically reloaded whenever the app is opened.

### Input data


### Expected output

### Usage
