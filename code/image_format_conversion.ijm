setBatchMode(true);
input = getDirectory("Select project folder.");

input_path = input+File.separator+"raw_files"
output_path = input+File.separator
filelist = getFileList(input_path) 

for (f=0; f< lengthOf(filelist); f++) {
    if (endsWith(filelist[f], ".img")) { 
        run("Bio-Formats Importer", "open="+input_path+File.separator+filelist[f]+" color_mode=Colorized rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT");
        cleanFileName = File.getNameWithoutExtension(filelist[f]);
        file_dir = File.makeDirectory(output_path+cleanFileName+File.separator);
        tif_dir = File.makeDirectory(output_path+cleanFileName+File.separator+"tif_file"+File.separator);
        saveAs("Tiff", output_path+cleanFileName+File.separator+"tif_file"+File.separator+cleanFileName+".tif");
    } 
}