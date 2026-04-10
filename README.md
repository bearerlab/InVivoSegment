# InVivo Atlas Segmentation

A Python GUI application for anatomical segmentation of MRI brain images using the *InVivo* Mouse Brain Atlas.

*If you use or modify this atlas or the InVivoSegment code, please cite this repository (see "Cite this Repository" above) and the published paper (DOI below).*

[![bioRxiv](https://img.shields.io/badge/bioRxiv-10.XXXX%2FXXXXX-red)](https://doi.org/10.XXXX/XXXXX)

## Overview

This software package performs anatomical segmentation of MR brain images using the *InVivo* Atlas (v10.4), a high-resolution Mn(II)-enhanced MRI of a mouse brain. The package provides an intuitive graphical user interface (GUI) for calculating summary statistics of image voxel intensities across 116 brain segments.

Although developed for longitudinal Mn(II)-enhanced MRI (MEMRI) data, the segmentation pipeline can be applied to any 3D brain images in NIfTI file format, including:

- Individual subject intensity images
- Group-level statistical maps (e.g., T-maps)
- Experimental condition data
- Validation datasets

## Features

- **Flexible Experimental Design**: Supports arbitrary combinations of groups and conditions
- **Multiple statistics**: Choose from 10 different segment-wise metrics (mean, median, standard deviation, quartiles, min/max, activation volumes, center-of-mass)
- **Threshold control**: Apply intensity or statistical thresholds to segmentation
- **Batch processing**: Process multiple images in a single analysis
- **Output management**: Automatically organized output directories with CSV results
- **User-friendly GUI**: Built with Tkinter for cross-platform compatibility

## Installation

### Requirements

- Python 3.8 or higher
- Dependencies: numpy, pandas, nibabel, matplotlib. Other packages are in the standard Python library.

### Clone from GitHub

```bash
git clone https://github.com/bearererlab/InVivoSegment.git
cd InVivoSegment
```

### Run from Source

Simply run the main script to start the GUI:

```bash
python InVivoSegment.py
```

Or, for more information about command-line options:

```bash
python InVivoSegment.py --info
python InVivoSegment.py --version
```

## Quick Start

1. **Launch the GUI**:

   ```bash
   python InVivoSegment.py
   ```

2. **Organize your data** following the structure described in the examples:
   - Create a working directory with subdirectories for InputData and atlas files
   - Place your NIfTI images in the InputData directory
   - Place the InVivo Atlas label image (NIfTI) and lookup table (CSV) in the atlas directory

3. **Use the GUI to**:
   - Select your working directory
   - Load the atlas lookup table and label image
   - Specify your experimental design (groups and conditions)
   - Choose statistics to compute
   - Apply any necessary thresholds
   - Run segmentation
   - Export results to CSV

## Example Workflow and Validation Datasets

This repository includes example data demonstrating:

- Multi-site validation datasets
- Noise simulation validation
- Analysis of statistical maps (SPM T-maps)
- Segmentation of intensity images across groups and conditions

See the [Examples.ipynb](./Examples.ipynb) notebook and `/examples` directory for detailed walkthroughs.

Once installed, open the [./Examples.ipynb](./Examples.ipynb) file and test run each section listed above (e.g., Multi-site validation, noise simulation, statistical maps). You can create a new segmentation output from using ```python InVivoSegment.py``` with the input files from each example provided. Create and walk through a copy of `Examples.ipynb` (e.g., `Validations.ipynb`) using your InVivoSegment CSV outputs as input data. Assess whether your output (csv and data summarized in `Validations.ipynb`) match our examples provided.

If you can do reproduce our results successfully, you can confidently move on to new applications.

## Documentation

### Directory Organization

Organize your data hierarchically to facilitate systematic file selection within the GUI:

```
working_directory/
├── atlas/
│   ├── InVivoAtlas_labels_v10.4.nii          # Atlas label image
│   └── InVivoAtlas_Sort_v10.4.csv            # Atlas lookup table
├── intensities/
│   ├── InputData/
│   │   ├── Grp1Con1/
│   │   │   ├── Grp1_Con1_01.nii
│   │   │   └── ...
│   │   └── Grp1Con2/
│   │       └── ...
│   ├── Masks/                                 # Auto-generated
│   └── OutputData/                            # Auto-generated
│       └── CSVs/
└── statistical_maps/
    ├── InputData/
    │   └── spmT_Grp1_Con2gt1_P05-T181-C8.nii
    ├── Masks/                                 # Auto-generated
    └── OutputData/                            # Auto-generated
        └── CSVs/
```

**Naming conventions**:

- `Grp#`: Group identifier
- `Con#`: Condition/contrast identifier  
- `P#`: Voxel-wise significance threshold
- `T#`: T-value or effect-size threshold
- `C#`: Cluster-size threshold (voxels)

### GUI Workflow (8 Steps)

**Step 0 - Prepare Data**: Organize your input files following the directory structure above. Be sure to have an aligned atlas label image and sorting table. See [InVivoAtlas_files](./InVivoAtlas_files/) for raw files, and [./examples/atlas/](./examples/atlas/) for aligned labels used in examples.

**Step 1 - Select Output Directory**: Choose your working directory. The GUI automatically creates `Masks` and `OutputData` subdirectories.

**Step 2 - Load Atlas Lookup Table**: Select your atlas sorting table (CSV). This defines segment identities and labeling conventions.

**Step 3 - Load Atlas Label Image**: Select your InVivo Atlas label image (NIfTI). This must be spatially aligned to your input images.

**Step 4 - Generate Masks**: Create binary masks for individual atlas segments. Optionally save as compressed NIfTI files (`.nii.gz`).

**Step 5 - Specify Experimental Design**: Define your groups and conditions. The GUI validates consistency with your input data.

**Step 6 - Select Statistics**: Choose which metrics to compute:

- Mean, Median, Standard Deviation
- Quartiles (Q1, Q3), Min, Max
- Activation volume (number of suprathreshold voxels)
- Fractional activation volume (percentage of segment)
- Center-of-mass (unweighted and signal-weighted)

**Step 7 - Apply Thresholds (Optional)**: Set intensity or statistical thresholds. This value is retained as metadata in the output CSV.

**Step 8 - Run Segmentation**: Select your input images and run segmentation. Results are saved to CSV format in `OutputData/CSVs/`.

**Note on Paired/Longitudinal Data**: Images must be selected in consistent order across conditions to preserve subject alignment.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on how to contribute.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## Authors

- **Taylor W. Uselman** ([twuselman@salud.unm.edu](mailto:twuselman@salud.unm.edu))
- **Elaine L. Bearer** ([elaine.bearer@gmail.com](mailto:elaine.bearer@gmail.com)) - corresponding author

## Support

For issues, questions, or feature requests, please open an issue on GitHub: [Issues](https://github.com/bearererlab/InVivoSegment/issues)
