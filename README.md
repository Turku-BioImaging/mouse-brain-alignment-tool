# Mouse Brain Alignment Tool
Processing of autoradiography (ARG) images from mouse brain tissue. This project includes a Napari-based user interface where ARG slides can be preprocessed and registered to Allen Brain Atlas regions.
<table>
  <tbody>
    <tr>
      <td style='padding: 10px;'><img src='/assets/turku_bioimaging_logo.jpg' style='height:50px;width:auto'/></td>
      <td><img src='/assets/isidore_logo.png' style='height:50px; width: auto;'/></td>
      <td><img src='/assets/euro_bioimaging_logo.png' style='height:50px; width: auto;'/></td>
    </tr>
  </tbody>
</table>

## User Manual
The user manual is found [here](https://github.com/Turku-BioImaging/mouse-brain-alignment-tool/blob/issue/24/user-documentation/USAGE.md).

## Developers / Contributors

### Environments
We use the mamba or conda package manager. If there are any changes in the `environment.yml`, please update your environment using one of the following lines:
```
mamba env update -f environment.yml --prune
conda env update -f environment.yml --prune
```
Activate the environment:
```
mamba activate mouse-brain-alignment-tool
```

### Running the modules
- In Start Menu, open `Miniforge Prompt`
```
mamba activate mouse-brain-alignment-tool
cd c:\Users\<username>\Desktop\mouse-brain-alignment-tool\src
python preprocess.py
python analyze.py
```

### Build
The build process depends on [PyInstaller](https://pyinstaller.org). In the local environment `pip install pyinstaller`. Currently, only _preprocess.exe_ can be built with PyInstaller. The analysis script _analyze.py_ requires the environment to be setup.
  
_preprocess.exe_
```
pyinstaller --onefile --windowed preprocess.py \
  --add-data "gui;gui" \
  --hidden-import openpyxl \ 
  --collect-all openpyxl \
  --name preprocess
```
