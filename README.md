# Mouse Brain Alignment Tool
Semi-automated processing of autoradiography (ARG) images from mouse brain tissue. This project includes a [Napari](https://napari.org)-based user interface where ARG slides can be preprocessed and registered to [Allen Brain Atlas](https://portal.brain-map.org/) regions.

<div style="display: flex; align-items: center; justify-content: center; width: 100%;">
  <a href="https://bioimaging.fi" target='_blank'>
    <img src="/assets/turku_bioimaging_logo.jpg" alt='Turku BioImaging' style="height: 50px; width: auto;">
  </a>
  <img src="/assets/spanner.png" style="height: 15px; width: auto;">
  <a href="https://turkupetcentre.fi" target="_blank">
    <img src="/assets/turku_pet_centre_logo.svg" alt="Turku PET Centre" style="height: 50px; width: auto;">
  </a>
  <img src="/assets/spanner.png" style="height: 15px; width: auto;">
  <a href="https://isidore-project.eu" target="_blank">
    <img src="/assets/isidore_logo.png" alt="ISIDORe Project" style="height: 50px; width: auto;">
  </a>
  <img src="/assets/spanner.png" style="height: 15px; width: auto;">
    <a href="https://eurobioimaging.eu" target="_blank">
  <img src="/assets/euro_bioimaging_logo.png" alt="Euro BioImaging" style="height: 50px; width: auto;">
  </a>
</div>

## User Manual
The user manual is found [here](https://github.com/Turku-BioImaging/mouse-brain-alignment-tool/blob/main/USAGE.md).

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

### Build
We use [PyInstaller](https://pyinstaller.org) _*.spec_ files for the build process. In the local environment `pip install pyinstaller`.
```
pyinstaller preprocess.spec
pyinstaller analyze.spec
```
This will generate two single-file executables _preprocess-0.2.2.exe_ and _analyze-0.2.2.exe_. Released builds are found in [here](https://github.com/Turku-BioImaging/mouse-brain-alignment-tool/releases).

## Funding
<a href="https://isidore-project.eu" target="_blank"><img src="/assets/isidore_logo.png" style="height: 50px; width: auto"></a>  

Funding for this project was provided by the _Integrated Services for Infectious Disease Outbreak Research_ [(ISIDORe)](https://isidore-project.eu) project of [Euro-BioImaging](https://eurobioimaging.eu).  


