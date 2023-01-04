// Converts a directory of *.IMG files into TIFFs using Bio-Formats

setBatchMode(true)

input_path = getDirectory('Select source folder');
output_path = getDirectory('Select output folder');

if (input_path == output_path) {
    exit('Error: Source and output folders must be different.');
}

file_list = getFileList(input_path);

for (f = 0; f < lengthOf(file_list); f++) {
    if (endsWith(file_list[f], '.img')) {
        command_string = 'open=' +
                            input_path +
                            File.separator +
                            file_list[f] +
                            ' color_mode=Colorized rois_import=[ROI manager]' +
                            ' view=Hyperstack stack_order=XYCZT';

        run('Bio-Formats Importer', command_string);
        
        filename = File.getNameWithoutExtension(file_list[f]) + '.tif';
        save_string = output_path + File.separator + filename;

        saveAs('Tiff', save_string);
    }
}
