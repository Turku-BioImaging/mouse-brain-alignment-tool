import os
import sys
import shutil
import numpy as np

PROJECT_PATH = 'project_data'

def padder(input_image, value):
    if input_image.shape[0] % 2 != 0:
        input_image = np.pad(input_image, pad_width=((0, 1), (0, 0)))
    if section.shape[1] % 2 != 0:
        input_image = np.pad(input_image, pad_width=((0, 0), (0, 1)))
    y = int((value - input_image.shape[0]) / 2)
    x = int((value - input_image.shape[1]) / 2)
    input_image = np.pad(input_image, pad_width=((y, y), (x, x)))
    return input_image

def _configure_dirs(
        data_path: str, 
        num_slides: int, 
        num_animals: int
    ):
    
    assert os.path.isdir(data_path), 'data_path must be a directory'
        
    if not os.path.isdir(PROJECT_PATH):
        os.mkdir(PROJECT_PATH)
    
    dir_name = os.path.basename(os.path.normpath(data_path))
    
    shutil.rmtree(os.path.join(PROJECT_PATH, dir_name), ignore_errors=True)   
    os.makedirs(os.path.join(PROJECT_PATH, dir_name))
    
    
    # configure project subdirs depending on number of animals
    if num_animals == 2:
        animal_right = sys.argv[4]
        animal_left = sys.argv[5]
        
        for a in (animal_right, animal_left):
            os.mkdir(os.path.join(PROJECT_PATH, dir_name, a))
            os.mkdir(os.path.join(PROJECT_PATH, dir_name, a, 'processed_images'))
            os.mkdir(os.path.join(PROJECT_PATH, dir_name, a, 'tiff'))
    
    else:
        os.makedirs(os.path.join(PROJECT_PATH, dir_name, 'tiff'))
        os.makedirs(os.path.join(PROJECT_PATH, dir_name, 'processed_images'))
        
    
    

if __name__ == '__main__':
    data_path = os.path.dirname(sys.argv[1])
    num_rows = int(sys.argv[2])
    num_animals = int(sys.argv[3])
    
    _configure_dirs(data_path, num_rows, num_animals)
    
    print(data_path, num_rows, num_animals)
    
    