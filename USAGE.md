# User Documentation

## Module 1 - Preprocessing
First here: how to set up images and excel.

### Input data
A single folder is required as input. This folder must contain any number of TIFF images and a single _data.xlsx_ file. Images __MUST__ use the extension _*.tif_, otherwise they will not be included in the preprocessing. The _data.xlsx_ is an Excel workbook that must follow a particular format. It includes the folowing columns:

- image_filename
- num_slides
- num_animals
- animal_left_name
- animal_right_name
  

![Example of data file](/assets/docs/screenshot-102249.png)  
_Example of Excel data file_

![Example contents of input folder](/assets/docs/screenshot-102625.png)  
_Example contents of input folder_

For every image, if the column *num_animals* has a value of _1_, then the columns *animal_left_name* and *animal_right_name* must be blank. A copy of the Excel template is located [here](excel_template.xlsx).

### Expected output

### Usage

------
In Miniforge prompt type in python preprocess.py to open preprocessing graphical user interface.
<img width="317" alt="preprocess_gui" src="https://github.com/Turku-BioImaging/mouse-brain-alignment-tool/assets/136598378/581beab6-5ac6-47db-8922-45bfb86e914a">
Select the directory where your images and data.xls file are. Select the folder where you want the preprocessed images to appear as output directory.

## Module 2 - Analysis
Some text here...
