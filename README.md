# Mouse Brain Segmentation Project
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

## Developers / Contributors

### Environments
We use the mamba or conda package manager. If there are any changes in the `environment.yml`, please update your environment using one of the following lines:
```
mamba env update -f environment.yml --prune
conda env update -f environment.yml --prune
```

### Build
The build process depends on [PyInstaller](https://pyinstaller.org). In the local environment `pip install pyinstaller`.  
  
_preprocess.exe_
```
pyinstaller --onefile --windowed setup_ui.py \
  --add-data "gui;gui"
  --name preprocess
```

_analyze.exe_
```
pyinstaller --onefile --windowed interact.py \
  --add-data "brain_atlas_files;brain_atlas_files"
  --name analyze
```
